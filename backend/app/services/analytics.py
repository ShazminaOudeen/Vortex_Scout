"""Analytics and reporting service for the Manager Portal (Module 5).

Provides dynamic calculations for:
- E1: Real KPIs (active voids, audit completion rate, revenue recovered, IRI rate, category breakdown)
- E2 & E6: Expected-vs-actual hourly velocity curves
- E4: Enriched recent reconciliations activity feed
- E5 & E6: SKU catalogue status, filtering metadata, and detail drill-downs
"""
from datetime import datetime, timezone, timedelta
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.core import store
from app.ml import feature_pipeline
from app.models.anomaly import (
    Anomaly,
    AuditFeedItem,
    CategoryShare,
    DashboardMetrics,
    VelocityPoint,
    VelocityResponse,
)
from app.models.sku import Sku, SkuDetail, SkuWithStatus


def compute_dashboard_metrics() -> DashboardMetrics:
    """Compute real dashboard KPIs without hardcoded or invented values (Feature E1)."""
    all_anomalies = store.list_anomalies()
    open_anomalies = [a for a in all_anomalies if a.status == "open"]
    resolved_anomalies = [a for a in all_anomalies if a.status != "open"]
    total_anomalies = len(all_anomalies)

    active_voids = len(open_anomalies)
    audit_completion_rate = (
        round(len(resolved_anomalies) / total_anomalies, 4) if total_anomalies > 0 else 0.0
    )

    # All catalogue SKUs
    all_skus = store.list_skus()
    sku_map: dict[str, Sku] = {s.id: s for s in all_skus}

    # Revenue recovered in LKR: value of goods recovered through restock actions
    # Calculated from restocked audit logs and/or restocked anomalies
    revenue_recovered = 0.0
    audit_rows = store.list_audit(limit=500)
    seen_anomalies = set()

    for row in audit_rows:
        if row.get("action") == "restocked":
            aid = str(row.get("anomaly_id", ""))
            seen_anomalies.add(aid)
            anom = store.get_anomaly(aid)
            sku = sku_map.get(anom.sku_id) if anom else None
            if sku:
                # If units explicitly recorded, use units; else use anomaly's ledger stock
                units = row.get("units")
                if units is None or units <= 0:
                    units = anom.ledger_stock if anom and anom.ledger_stock > 0 else 1
                revenue_recovered += units * float(sku.unit_price)

    # Also account for any resolved anomalies in memory/db marked restocked that might not be in audit_rows
    for anom in resolved_anomalies:
        if anom.status == "restocked" and anom.id not in seen_anomalies:
            sku = sku_map.get(anom.sku_id)
            if sku:
                units = anom.ledger_stock if anom.ledger_stock > 0 else 1
                revenue_recovered += units * float(sku.unit_price)

    # IRI (Inventory Record Inaccuracy) rate: fraction of catalogue items experiencing phantom discrepancies
    open_sku_ids = {a.sku_id for a in open_anomalies}
    iri_rate = (
        round(len(open_sku_ids) / len(all_skus), 4) if len(all_skus) > 0 else 0.0
    )

    # Category breakdown: share of active voids per category
    # If no active voids, fall back to historical anomalies; if none, empty list
    source_anomalies = open_anomalies if open_anomalies else all_anomalies
    category_breakdown: list[CategoryShare] = []
    if source_anomalies:
        cat_counts: dict[str, int] = {}
        for a in source_anomalies:
            cat_counts[a.category] = cat_counts.get(a.category, 0) + 1
        total_source = len(source_anomalies)
        for cat, cnt in sorted(cat_counts.items(), key=lambda kv: kv[1], reverse=True):
            category_breakdown.append(
                CategoryShare(category=cat, share=round((cnt / total_source) * 100, 1))
            )

    return DashboardMetrics(
        revenue_recovered_lkr=round(revenue_recovered, 2),
        active_voids=active_voids,
        audit_completion_rate=audit_completion_rate,
        iri_rate=iri_rate,
        category_breakdown=category_breakdown,
    )


def compute_sku_velocity(sku_id: str, window_hours: int = 24) -> VelocityResponse:
    """Compute real expected vs actual sales velocity for a SKU (Feature E2 & E6)."""
    sku = store.get_sku(sku_id)
    if sku is None:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id!r} not found")

    v = feature_pipeline.get_velocity(open_only=True)
    if v.empty:
        return VelocityResponse(
            sku_id=sku.id, sku_name=sku.name, points=[], has_data=False
        )

    sku_v = v[v["sku_id"] == sku_id].sort_values("hour").reset_index(drop=True)
    if sku_v.empty:
        return VelocityResponse(
            sku_id=sku.id, sku_name=sku.name, points=[], has_data=False
        )

    # Learn store-wide hourly rhythm from history prior to quiet streaks
    v_copy = v.copy()
    v_copy["slot"] = (v_copy["day_of_week"] >= 5).astype(int) * 24 + v_copy["hour_of_day"]
    sold = v_copy["units"] > 0
    cum_sales = sold.groupby(v_copy["sku_id"]).cumsum()
    total_sales = cum_sales.groupby(v_copy["sku_id"]).transform("max")
    v_copy["trailing"] = (cum_sales == total_sales) & ~sold

    history = v_copy[~v_copy["trailing"]]
    overall = history["units"].mean() if not history.empty else 0.0

    if overall > 0:
        profile = (history.groupby("slot")["units"].mean() / overall).reindex(range(48)).fillna(1.0)
        sku_hist = history[history["sku_id"] == sku_id]
        p_hist = sku_hist["slot"].map(profile).sum()
        u_hist = sku_hist["units"].sum()
        base_rate = (u_hist / p_hist) if p_hist > 0 else (u_hist / len(sku_hist) if len(sku_hist) > 0 else 0.0)
    else:
        profile = pd.Series(1.0, index=range(48))
        base_rate = sku_v["units"].mean()

    recent = sku_v.tail(window_hours)
    points: list[VelocityPoint] = []
    for _, row in recent.iterrows():
        slot = int((row["day_of_week"] >= 5) * 24 + row["hour_of_day"])
        prof_factor = float(profile.get(slot, 1.0))
        expected_val = round(max(0.0, float(base_rate * prof_factor)), 2)
        h_dt = pd.to_datetime(row["hour"])
        points.append(
            VelocityPoint(
                timestamp=h_dt.isoformat(),
                hour=h_dt.strftime("%H:00"),
                expected=expected_val,
                actual=int(row["units"]),
            )
        )

    return VelocityResponse(
        sku_id=sku.id,
        sku_name=sku.name,
        points=points,
        has_data=len(points) > 0,
    )


def get_audit_feed(limit: int = 50, sku_id: str | None = None) -> list[AuditFeedItem]:
    """Retrieve human-readable reconciliation activity feed (Feature E4)."""
    raw_logs = store.list_audit(limit=limit)
    anomalies_map = {a.id: a for a in store.list_anomalies()}
    skus_map = {s.id: s for s in store.list_skus()}

    feed: list[AuditFeedItem] = []
    for r in raw_logs:
        aid = str(r.get("anomaly_id", ""))
        anom = anomalies_map.get(aid) or store.get_anomaly(aid)
        
        # If anomaly not found, attempt to construct fallback
        if anom:
            s_id = anom.sku_id
            s_name = anom.sku_name
            cat = anom.category
            aisle = anom.aisle
            bay = anom.bay
        else:
            s_id = "unknown"
            s_name = "Catalog Product"
            cat = "General"
            aisle = "-"
            bay = "-"

        if sku_id and s_id != sku_id:
            continue

        action = str(r.get("action", ""))
        associate = r.get("associate")
        units = r.get("units")
        
        # Parse created_at
        created_val = r.get("created_at")
        if isinstance(created_val, datetime):
            created_at = created_val
        elif isinstance(created_val, str):
            try:
                created_at = datetime.fromisoformat(created_val.replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.now(timezone.utc)
        else:
            created_at = datetime.now(timezone.utc)

        # Build clear human-readable narrative
        assoc_suffix = f" by {associate}" if associate else ""
        if action == "restocked":
            u_prefix = f"{units} units of " if units else ""
            summary = f"{u_prefix}{s_name} restocked from Bay {bay}{assoc_suffix}"
        elif action == "damaged":
            u_prefix = f"{units} units of " if units else ""
            summary = f"{u_prefix}{s_name} written off (damaged) in Bay {bay}{assoc_suffix}"
        elif action == "false_alarm":
            summary = f"False alarm dismissed for {s_name} in Bay {bay}{assoc_suffix}"
        else:
            summary = f"Audit action {action!r} recorded for {s_name}{assoc_suffix}"

        feed.append(
            AuditFeedItem(
                id=r.get("id", len(feed) + 1),
                anomaly_id=aid,
                sku_id=s_id,
                sku_name=s_name,
                category=cat,
                aisle=aisle,
                bay=bay,
                action=action,
                associate=associate,
                units=units,
                created_at=created_at,
                summary=summary,
            )
        )

    return feed


def list_skus_with_status() -> list[SkuWithStatus]:
    """Retrieve full 200-SKU catalogue with active anomaly and risk status (Feature E5)."""
    all_skus = store.list_skus()
    all_anomalies = store.list_anomalies()
    
    # Index anomalies by SKU
    open_by_sku: dict[str, Anomaly] = {}
    latest_by_sku: dict[str, Anomaly] = {}
    for a in all_anomalies:
        if a.status == "open":
            open_by_sku[a.sku_id] = a
        latest_by_sku[a.sku_id] = a

    # Identify recently reconciled SKUs (past 24h)
    now = datetime.now(timezone.utc)
    reconciled_today_skus: set[str] = set()
    for a in all_anomalies:
        if a.status != "open" and a.resolved_at:
            dt = a.resolved_at
            if isinstance(dt, str):
                try:
                    dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                except Exception:
                    continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if (now - dt).total_seconds() <= 86400:
                reconciled_today_skus.add(a.sku_id)

    # Check recent audit log as well
    for r in store.list_audit(limit=100):
        aid = str(r.get("anomaly_id", ""))
        anom = latest_by_sku.get(aid) or store.get_anomaly(aid)
        if anom:
            reconciled_today_skus.add(anom.sku_id)

    items: list[SkuWithStatus] = []
    for s in all_skus:
        open_anom = open_by_sku.get(s.id)
        latest_anom = latest_by_sku.get(s.id)
        
        if open_anom:
            p_void = float(open_anom.p_void)
            status = open_anom.status
            anom_id = open_anom.id
            has_open = True
            risk_level: Literal["critical", "high", "normal"] = (
                "critical" if p_void >= 0.75 else ("high" if p_void >= 0.50 else "normal")
            )
        elif latest_anom:
            p_void = float(latest_anom.p_void) if latest_anom.status == "open" else 0.0
            status = latest_anom.status
            anom_id = latest_anom.id
            has_open = False
            risk_level = "normal"
        else:
            p_void = 0.0
            status = None
            anom_id = None
            has_open = False
            risk_level = "normal"

        is_reconciled = (s.id in reconciled_today_skus)

        items.append(
            SkuWithStatus(
                id=s.id,
                barcode=s.barcode,
                name=s.name,
                category=s.category,
                aisle=s.aisle,
                bay=s.bay,
                ledger_stock=s.ledger_stock,
                unit_cost=s.unit_cost,
                unit_price=s.unit_price,
                p_void=round(p_void, 3),
                anomaly_status=status,
                anomaly_id=anom_id,
                has_open_anomaly=has_open,
                reconciled_today=is_reconciled,
                risk_level=risk_level,
            )
        )

    return items


def get_sku_detail(sku_id: str) -> SkuDetail:
    """Retrieve full detail for a SKU including open anomaly and audit history (Feature E6)."""
    sku = store.get_sku(sku_id)
    if sku is None:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id!r} not found")

    skus_with_status = {s.id: s for s in list_skus_with_status()}
    status_sku = skus_with_status.get(sku.id)
    if status_sku is None:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id!r} not found in catalog")

    # Find open anomaly if any
    open_anom = None
    if status_sku.anomaly_id:
        open_anom = store.get_anomaly(status_sku.anomaly_id)
        if open_anom and open_anom.status != "open":
            open_anom = None

    history = get_audit_feed(limit=50, sku_id=sku.id)

    return SkuDetail(
        sku=status_sku,
        open_anomaly=open_anom,
        audit_history=history,
    )
