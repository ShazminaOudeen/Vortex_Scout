"""A tiny in-process stand-in for the supabase-py client, just big enough for app/core/store.py.

It mimics the parts of PostgREST behaviour the store depends on, so the Supabase code paths run in
CI without network or keys:
  * fluent API: table().select/insert/upsert/update/delete + eq/neq/gt/gte/lt/in_/order/range/limit/execute
  * responses capped at 1000 rows per request (the store must paginate)
  * timestamptz columns are returned as ISO strings with a +00:00 offset (naive input is read as UTC)
  * column defaults (uuid / serial ids, status='open', detected_at) and the schema's CHECK constraints

It is NOT Postgres: no foreign keys, no transactions. A green run here does not replace a smoke test
against a real project.
"""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

TS_COLUMNS = {"ts", "hour", "detected_at", "resolved_at", "created_at"}
PRIMARY_KEYS = {
    "stores": ("id",), "skus": ("id",), "hourly_velocity": ("store_id", "sku_id", "hour"),
    "stockout_anomalies": ("id",), "pos_transactions": ("id",), "audit_log": ("id",),
}
SERIAL = {"pos_transactions", "audit_log"}
MAX_ROWS = 1000


def _ts(value):
    if value is None:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _norm(row: dict) -> dict:
    return {k: (_ts(v).isoformat() if k in TS_COLUMNS and v is not None else v) for k, v in row.items()}


def _cmp(col, value):
    return _ts(value) if col in TS_COLUMNS else value


class _Query:
    def __init__(self, db, table):
        self.db, self.name = db, table
        self.op, self.payload, self.on_conflict = "select", None, None
        self.cols, self.filters, self.order_by, self.lo, self.hi = None, [], [], 0, None

    # --- operation selectors
    def select(self, cols="*", **_):
        self.op, self.cols = "select", None if cols == "*" else [c.strip() for c in cols.split(",")]
        return self

    def insert(self, rows):
        self.op, self.payload = "insert", rows if isinstance(rows, list) else [rows]
        return self

    def upsert(self, rows, on_conflict=None):
        self.op, self.payload = "upsert", rows if isinstance(rows, list) else [rows]
        self.on_conflict = tuple(on_conflict.split(",")) if on_conflict else None
        return self

    def update(self, values):
        self.op, self.payload = "update", values
        return self

    def delete(self):
        self.op = "delete"
        return self

    # --- filters / modifiers
    def _f(self, kind, col, val):
        self.filters.append((kind, col, val))
        return self

    def eq(self, c, v): return self._f("eq", c, v)
    def neq(self, c, v): return self._f("neq", c, v)
    def gt(self, c, v): return self._f("gt", c, v)
    def gte(self, c, v): return self._f("gte", c, v)
    def lt(self, c, v): return self._f("lt", c, v)
    def in_(self, c, v): return self._f("in", c, list(v))

    def order(self, col, desc=False):
        self.order_by.append((col, desc))  # chained order() calls add sort keys, like PostgREST
        return self

    def range(self, lo, hi):
        self.lo, self.hi = lo, hi
        return self

    def limit(self, n):
        self.lo, self.hi = 0, n - 1
        return self

    # --- execution
    def _match(self, row):
        for kind, col, val in self.filters:
            have = row.get(col)
            want = [_cmp(col, x) for x in val] if kind == "in" else _cmp(col, val)
            have = _cmp(col, have) if have is not None else None
            if have is None and kind != "neq":
                return False
            ok = {"eq": lambda: have == want, "neq": lambda: have != want, "gt": lambda: have > want,
                  "gte": lambda: have >= want, "lt": lambda: have < want, "in": lambda: have in want}[kind]()
            if not ok:
                return False
        return True

    def _defaults(self, row):
        row = _norm(row)
        t = self.name
        if t in SERIAL and "id" not in row:
            self.db.serial[t] += 1
            row["id"] = self.db.serial[t]
        if t == "stockout_anomalies":
            row.setdefault("id", str(uuid.uuid4()))
            row.setdefault("status", "open")
            row.setdefault("detected_at", datetime.now(timezone.utc).isoformat())
            row.setdefault("resolved_at", None)
            assert row["status"] in ("open", "restocked", "damaged", "false_alarm"), "status check"
            assert 0 <= row["p_void"] <= 1, "p_void check"
        if t == "pos_transactions":
            assert row["quantity_sold"] > 0, "quantity_sold check"
        if t == "audit_log":
            row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            assert row["action"] in ("restocked", "damaged", "false_alarm"), "action check"
        if t == "skus":
            row.setdefault("ledger_stock", 0)
        return row

    def execute(self):
        rows = self.db.tables[self.name]
        pk = PRIMARY_KEYS[self.name]
        if self.op == "select":
            out = [r for r in rows if self._match(r)]
            for col, desc in reversed(self.order_by):  # stable sorts, least-significant key first
                out.sort(key=lambda r: (r.get(col) is None, _cmp(col, r.get(col))), reverse=desc)
            hi = MAX_ROWS - 1 if self.hi is None else min(self.hi, self.lo + MAX_ROWS - 1)
            out = out[self.lo:hi + 1]
            if self.cols:
                out = [{c: r[c] for c in self.cols} for r in out]
            return SimpleNamespace(data=[dict(r) for r in out])
        if self.op == "insert":
            new = [self._defaults(r) for r in self.payload]
            rows.extend(new)
            return SimpleNamespace(data=[dict(r) for r in new])
        if self.op == "upsert":
            keys = self.on_conflict or pk
            idx = self.db.index(self.name, keys)
            done = []
            for raw in self.payload:
                new = self._defaults(raw)
                k = tuple(new.get(c) for c in keys)
                if k in idx:
                    idx[k].update(new)
                    done.append(idx[k])
                else:
                    rows.append(new)
                    idx[k] = new
                    done.append(new)
            return SimpleNamespace(data=[dict(r) for r in done])
        if self.op == "update":
            hit = [r for r in rows if self._match(r)]
            for r in hit:
                r.update(_norm(self.payload))
            return SimpleNamespace(data=[dict(r) for r in hit])
        if self.op == "delete":
            if not self.filters:
                raise RuntimeError("DELETE requires a filter (PostgREST rejects unfiltered deletes)")
            gone = [r for r in rows if self._match(r)]
            gone_ids = {id(r) for r in gone}
            self.db.tables[self.name] = [r for r in rows if id(r) not in gone_ids]
            self.db.indexes.pop(self.name, None)
            return SimpleNamespace(data=gone)
        raise AssertionError(self.op)


class FakeSupabase:
    def __init__(self):
        self.tables = {t: [] for t in PRIMARY_KEYS}
        self.serial = {t: 0 for t in SERIAL}
        self.calls: list[tuple[str, str]] = []  # (table, op) per executed request
        self.indexes: dict[str, dict[tuple, dict]] = {}

    def index(self, table, keys):
        """Conflict-key -> row map for fast upserts; rebuilt if rows were added another way."""
        cached = self.indexes.get(table)
        if cached is None or cached["keys"] != keys or len(cached["map"]) != len(self.tables[table]):
            cached = {"keys": keys, "map": {tuple(r.get(c) for c in keys): r for r in self.tables[table]}}
            self.indexes[table] = cached
        return cached["map"]

    def table(self, name):
        q = _Query(self, name)
        execute = q.execute

        def logged():
            self.calls.append((name, q.op))
            return execute()

        q.execute = logged
        return q
