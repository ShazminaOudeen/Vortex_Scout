"""Data-access layer.

Every function talks to Supabase when `get_supabase()` returns a client
(SUPABASE_URL + SUPABASE_KEY set) and to an in-memory store otherwise, so the
whole app, and the test suite, runs with no keys. The API layer never touches
either backend directly; it only calls the functions below.

Conventions
  * POS timestamps are naive store-clock datetimes (see app/core/timeutil.py).
  * `since` is inclusive and `until` exclusive wherever they appear.
  * Table/column names follow supabase/schema.sql (pos_transactions.ts and
    .quantity_sold map to the API's `timestamp` and `quantity`).
"""
import uuid
from collections import defaultdict
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.core.database import get_supabase
from app.core.timeutil import floor_hour, from_db, to_db
from app.generator.catalog import DEMO_STORES, load_skus
from app.models.anomaly import Anomaly
from app.models.sku import Sku

_now = lambda: datetime.now(timezone.utc)  # noqa: E731
_PAGE = 1000  # PostgREST returns at most 1000 rows per request

VelocityKey = tuple[str, str, datetime]  # (store_id, sku_id, hour start)

# (id, sku_id, p_void, hours_since_last_sale) -- demo anomalies restored by reset()
_DEMO_ANOMALIES = [("a1", "s1", 0.93, 14), ("a2", "s2", 0.88, 9), ("a3", "s3", 0.81, 11)]

# --------------------------------------------------------------------------
# in-memory backing store (also what tests inspect when running without keys)
# --------------------------------------------------------------------------
STORES: dict[str, dict] = {}
SKUS: dict[str, Sku] = {}
TRANSACTIONS: list[dict] = []
HOURLY: dict[VelocityKey, int] = {}
ANOMALIES: dict[str, Anomaly] = {}
AUDIT_LOG: list[dict] = []


def _sb():
    return get_supabase()


def using_supabase() -> bool:
    return _sb() is not None


def _sku_order(s: Sku) -> tuple[int, str]:
    tail = s.id[1:]
    return (int(tail), s.id) if s.id[:1] == "s" and tail.isdigit() else (10**9, s.id)


def _paged(make_query: Callable[[], Any]) -> list[dict]:
    """Fetch every row of a query (PostgREST caps a single response at 1000)."""
    out: list[dict] = []
    while True:
        page = make_query().range(len(out), len(out) + _PAGE - 1).execute().data or []
        out.extend(page)
        if len(page) < _PAGE:
            return out


def _chunks(rows: list, size: int):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


# --------------------------------------------------------------------------
# stores
# --------------------------------------------------------------------------
def list_stores() -> list[dict]:
    if (sb := _sb()) is not None:
        return sb.table("stores").select("*").execute().data or []
    return list(STORES.values())


def upsert_stores(rows: list[dict]) -> None:
    if (sb := _sb()) is not None:
        sb.table("stores").upsert(rows, on_conflict="id").execute()
        return
    for r in rows:
        STORES[r["id"]] = dict(r)


# --------------------------------------------------------------------------
# SKUs / ledger
# --------------------------------------------------------------------------
def list_skus() -> list[Sku]:
    if (sb := _sb()) is not None:
        rows = _paged(lambda: sb.table("skus").select("*").order("id"))
        return sorted((Sku.model_validate(r) for r in rows), key=_sku_order)
    return sorted(SKUS.values(), key=_sku_order)


def get_sku(sku_id: str) -> Sku | None:
    if (sb := _sb()) is not None:
        rows = sb.table("skus").select("*").eq("id", sku_id).execute().data
        return Sku.model_validate(rows[0]) if rows else None
    return SKUS.get(sku_id)


def upsert_skus(skus: list[Sku]) -> None:
    if (sb := _sb()) is not None:
        for chunk in _chunks([s.model_dump() for s in skus], get_settings().ingest_chunk_size):
            sb.table("skus").upsert(chunk, on_conflict="id").execute()
        return
    for s in skus:
        SKUS[s.id] = s.model_copy()


def set_ledger_stock(sku_id: str, qty: int) -> None:
    qty = max(0, int(qty))
    if (sb := _sb()) is not None:
        sb.table("skus").update({"ledger_stock": qty}).eq("id", sku_id).execute()
    elif sku_id in SKUS:
        SKUS[sku_id].ledger_stock = qty


def adjust_ledger_stock(sku_id: str, delta: int) -> int | None:
    """Add `delta` to the SKU's ledger stock (never below 0); returns the new value.

    Read-modify-write, not atomic: fine for the demo's single operator.
    """
    sku = get_sku(sku_id)
    if sku is None:
        return None
    new = max(0, sku.ledger_stock + int(delta))
    set_ledger_stock(sku_id, new)
    return new


# --------------------------------------------------------------------------
# POS transactions + hourly_velocity (feature store)
# --------------------------------------------------------------------------
def insert_transactions(rows: list[dict]) -> int:
    """rows: dicts with store_id, sku_id, timestamp (naive datetime), quantity, unit_price."""
    if not rows:
        return 0
    if (sb := _sb()) is not None:
        payload = [{"store_id": r["store_id"], "sku_id": r["sku_id"], "ts": to_db(r["timestamp"]),
                    "quantity_sold": r["quantity"], "unit_price": r["unit_price"]} for r in rows]
        sb.table("pos_transactions").insert(payload).execute()
    else:
        TRANSACTIONS.extend(dict(r) for r in rows)
    return len(rows)


def refresh_hourly_velocity(keys: Iterable[VelocityKey]) -> int:
    """Recompute hourly_velocity for the given (store, sku, hour) buckets from the raw
    transactions and upsert them. Recomputing (rather than incrementing) keeps the table
    correct if a batch is retried. Returns the number of buckets written."""
    keyset = set(keys)
    if not keyset:
        return 0
    agg: dict[VelocityKey, int] = defaultdict(int)
    if (sb := _sb()) is not None:
        lo = min(k[2] for k in keyset)
        hi = max(k[2] for k in keyset) + timedelta(hours=1)
        skus = sorted({k[1] for k in keyset})
        stores = sorted({k[0] for k in keyset})
        rows = _paged(lambda: sb.table("pos_transactions").select("store_id,sku_id,ts,quantity_sold")
                      .in_("store_id", stores).in_("sku_id", skus)
                      .gte("ts", to_db(lo)).lt("ts", to_db(hi)).order("id"))
        for r in rows:
            k = (r["store_id"], r["sku_id"], floor_hour(from_db(r["ts"])))
            if k in keyset:
                agg[k] += r["quantity_sold"]
        payload = [{"store_id": s, "sku_id": k, "hour": to_db(h), "units": u} for (s, k, h), u in agg.items()]
        for chunk in _chunks(payload, get_settings().ingest_chunk_size):
            sb.table("hourly_velocity").upsert(chunk, on_conflict="store_id,sku_id,hour").execute()
    else:
        for t in TRANSACTIONS:
            k = (t["store_id"], t["sku_id"], floor_hour(t["timestamp"]))
            if k in keyset:
                agg[k] += t["quantity"]
        HOURLY.update(agg)
    return len(agg)


def list_hourly_velocity(store_id: str | None = None, sku_id: str | None = None,
                         since: datetime | None = None, until: datetime | None = None) -> list[dict]:
    """Sparse rows [{store_id, sku_id, hour, units}]: only hours that had sales."""
    if (sb := _sb()) is not None:
        def q():
            query = sb.table("hourly_velocity").select("*")
            if store_id:
                query = query.eq("store_id", store_id)
            if sku_id:
                query = query.eq("sku_id", sku_id)
            if since:
                query = query.gte("hour", to_db(since))
            if until:
                query = query.lt("hour", to_db(until))
            return query.order("hour").order("sku_id").order("store_id")
        return [{**r, "hour": from_db(r["hour"])} for r in _paged(q)]
    return [
        {"store_id": s, "sku_id": k, "hour": h, "units": u}
        for (s, k, h), u in sorted(HOURLY.items(), key=lambda kv: kv[0][2])
        if (not store_id or s == store_id) and (not sku_id or k == sku_id)
        and (not since or h >= since) and (not until or h < until)
    ]


def latest_velocity_hour(store_id: str | None = None) -> datetime | None:
    """Start of the most recent hour with any recorded sales (the data clock)."""
    if (sb := _sb()) is not None:
        q = sb.table("hourly_velocity").select("hour").order("hour", desc=True).limit(1)
        if store_id:
            q = q.eq("store_id", store_id)
        rows = q.execute().data
        return from_db(rows[0]["hour"]) if rows else None
    hours = [h for (s, _, h) in HOURLY if not store_id or s == store_id]
    return max(hours) if hours else None


# --------------------------------------------------------------------------
# anomalies
# --------------------------------------------------------------------------
def _anomaly_from_row(r: dict, skus: dict[str, Sku]) -> Anomaly:
    sku = skus[r["sku_id"]]
    return Anomaly(
        id=str(r["id"]), sku_id=sku.id, sku_name=sku.name, category=sku.category,
        aisle=sku.aisle, bay=sku.bay,
        ledger_stock=r["ledger_stock_at_detection"] if r.get("ledger_stock_at_detection") is not None else sku.ledger_stock,
        hours_since_last_sale=float(r["hours_since_last_sale"] or 0), p_void=float(r["p_void"]),
        status=r["status"], detected_at=r["detected_at"], resolved_at=r.get("resolved_at"),
        void_type=r.get("void_type", "frozen"),
        suggested_action=r.get("suggested_action", "restocked"),
    )


def list_anomalies(status: str | None = None) -> list[Anomaly]:
    if (sb := _sb()) is not None:
        skus = {s.id: s for s in list_skus()}
        rows = _paged(lambda: (sb.table("stockout_anomalies").select("*").eq("status", status)
                               if status else sb.table("stockout_anomalies").select("*"))
                      .order("detected_at").order("id"))
        return [_anomaly_from_row(r, skus) for r in rows]
    return [a for a in ANOMALIES.values() if status is None or a.status == status]


def get_anomaly(anomaly_id: str) -> Anomaly | None:
    if (sb := _sb()) is not None:
        try:
            rows = sb.table("stockout_anomalies").select("*").eq("id", anomaly_id).execute().data
        except Exception:
            return None
        return _anomaly_from_row(rows[0], {s.id: s for s in list_skus()}) if rows else None
    return ANOMALIES.get(anomaly_id)


def create_anomaly(sku_id: str, p_void: float, hours_since_last_sale: float,
                   ledger_stock: int | None = None, store_id: str | None = None,
                   anomaly_id: str | None = None, void_type: str = "frozen",
                   suggested_action: str = "restocked") -> Anomaly:
    """Open a new anomaly for a SKU. `ledger_stock` defaults to the SKU's current ledger."""
    sku = get_sku(sku_id)
    if sku is None:
        raise ValueError(f"unknown sku_id {sku_id!r}")
    ledger = sku.ledger_stock if ledger_stock is None else ledger_stock
    if (sb := _sb()) is not None:
        row = sb.table("stockout_anomalies").insert({
            "store_id": store_id or get_settings().default_store_id, "sku_id": sku_id,
            "p_void": round(p_void, 3), "hours_since_last_sale": round(hours_since_last_sale, 1),
            "ledger_stock_at_detection": ledger,
        }).execute().data[0]
        return _anomaly_from_row(row, {sku.id: sku})
    a = Anomaly(id=anomaly_id or uuid.uuid4().hex[:12], sku_id=sku.id, sku_name=sku.name, category=sku.category,
                aisle=sku.aisle, bay=sku.bay, ledger_stock=ledger, hours_since_last_sale=hours_since_last_sale,
                p_void=p_void, detected_at=_now(), void_type=void_type, suggested_action=suggested_action)
    ANOMALIES[a.id] = a
    return a


def update_anomaly(anomaly_id: str, p_void: float, hours_since_last_sale: float, ledger_stock: int,
                   void_type: str | None = None, suggested_action: str | None = None) -> bool:
    """Refresh the numbers on an *open* anomaly (keeps its id and detected_at). Returns True if updated."""
    if (sb := _sb()) is not None:
        payload = {"p_void": round(p_void, 3), "hours_since_last_sale": round(hours_since_last_sale, 1),
                   "ledger_stock_at_detection": ledger_stock}
        rows = (sb.table("stockout_anomalies")
                .update(payload)
                .eq("id", anomaly_id).eq("status", "open").execute().data)
        return bool(rows)
    a = ANOMALIES.get(anomaly_id)
    if a is None or a.status != "open":
        return False
    a.p_void, a.hours_since_last_sale, a.ledger_stock = round(p_void, 3), round(hours_since_last_sale, 1), ledger_stock
    if void_type is not None:
        a.void_type = void_type
    if suggested_action is not None:
        a.suggested_action = suggested_action
    return True


def delete_anomaly(anomaly_id: str) -> bool:
    """Remove an *open* anomaly the detector no longer supports. Resolved anomalies are never deleted."""
    if (sb := _sb()) is not None:
        rows = sb.table("stockout_anomalies").delete().eq("id", anomaly_id).eq("status", "open").execute().data
        return bool(rows)
    a = ANOMALIES.get(anomaly_id)
    if a is None or a.status != "open":
        return False
    del ANOMALIES[anomaly_id]
    return True


def resolve_anomaly(anomaly_id: str, status: str) -> Anomaly | None:
    """Close an *open* anomaly. Returns the updated anomaly, or None if it doesn't exist or was already resolved."""
    now = _now()
    if (sb := _sb()) is not None:
        rows = (sb.table("stockout_anomalies").update({"status": status, "resolved_at": now.isoformat()})
                .eq("id", anomaly_id).eq("status", "open").execute().data)
        return _anomaly_from_row(rows[0], {s.id: s for s in list_skus()}) if rows else None
    a = ANOMALIES.get(anomaly_id)
    if a is None or a.status != "open":
        return None
    a.status, a.resolved_at = status, now
    return a


# --------------------------------------------------------------------------
# audit log
# --------------------------------------------------------------------------
def append_audit(anomaly_id: str, action: str, associate: str | None = None,
                 units: int | None = None) -> dict:
    row = {"anomaly_id": anomaly_id, "action": action, "associate": associate, "units": units}
    if (sb := _sb()) is not None:
        return sb.table("audit_log").insert(row).execute().data[0]
    row = {"id": len(AUDIT_LOG) + 1, **row, "created_at": _now().isoformat()}
    AUDIT_LOG.append(row)
    return row


def list_audit(limit: int = 50) -> list[dict]:
    """Newest first."""
    if (sb := _sb()) is not None:
        return sb.table("audit_log").select("*").order("created_at", desc=True).limit(limit).execute().data or []
    return list(reversed(AUDIT_LOG))[:limit]


def audit_action_counts() -> dict[str, int]:
    """{'restocked': n, 'damaged': n, 'false_alarm': n} over the whole audit log."""
    counts = {"restocked": 0, "damaged": 0, "false_alarm": 0}
    if (sb := _sb()) is not None:
        rows = _paged(lambda: sb.table("audit_log").select("action").order("id"))
    else:
        rows = AUDIT_LOG
    for r in rows:
        counts[r["action"]] = counts.get(r["action"], 0) + 1
    return counts


# --------------------------------------------------------------------------
# reset / bootstrap
# --------------------------------------------------------------------------
def _reset_memory() -> None:
    """Rebuild the in-memory store from the catalog."""
    TRANSACTIONS.clear()
    HOURLY.clear()
    ANOMALIES.clear()
    AUDIT_LOG.clear()
    STORES.clear()
    SKUS.clear()
    STORES.update({s["id"]: dict(s) for s in DEMO_STORES})
    SKUS.update({s.id: s for s in load_skus()})
    for aid, sku_id, p_void, hours in _DEMO_ANOMALIES:
        sku = SKUS[sku_id]
        ANOMALIES[aid] = Anomaly(
            id=aid, sku_id=sku.id, sku_name=sku.name, category=sku.category, aisle=sku.aisle, bay=sku.bay,
            ledger_stock=sku.ledger_stock, hours_since_last_sale=hours, p_void=p_void, detected_at=_now())


def reset() -> None:
    """Wipe all demo data, restore the catalog and ledger stock."""
    if (sb := _sb()) is None:
        _reset_memory()
        return
    sb.table("audit_log").delete().gt("id", -1).execute()
    sb.table("stockout_anomalies").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    sb.table("hourly_velocity").delete().gte("units", 0).execute()
    sb.table("pos_transactions").delete().gt("id", -1).execute()
    upsert_stores(DEMO_STORES)
    upsert_skus(load_skus())
    for _, sku_id, p_void, hours in _DEMO_ANOMALIES:
        create_anomaly(sku_id, p_void, hours)


_reset_memory()
