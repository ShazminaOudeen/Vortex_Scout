"""Aggregate raw POS rows into hourly sales velocity per SKU."""
from datetime import datetime

import pandas as pd

from app.core import store

OPEN_HOUR, CLOSE_HOUR = 8, 22  # store trading hours: 08:00-22:00
PEAK_HOURS = frozenset({11, 12, 18, 19, 20})


def hourly_velocity(transactions: pd.DataFrame) -> pd.DataFrame:
    """transactions: columns [timestamp, sku_id, store_id, quantity].

    Returns a dense (sku_id, hour) frame with explicit zero-sale hours --
    the zeros are exactly what the ZIP model needs to see.
    """
    df = transactions.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.floor("h")
    g = df.groupby(["sku_id", "hour"], as_index=False)["quantity"].sum()
    out = []
    for sku_id, part in g.groupby("sku_id"):
        idx = pd.date_range(part["hour"].min(), part["hour"].max(), freq="h")
        s = part.set_index("hour")["quantity"].reindex(idx, fill_value=0)
        out.append(pd.DataFrame({"sku_id": sku_id, "hour": idx, "units": s.values}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["sku_id", "hour", "units"])


def add_time_features(velocity: pd.DataFrame) -> pd.DataFrame:
    v = velocity.copy()
    v["hour_of_day"] = v["hour"].dt.hour
    v["day_of_week"] = v["hour"].dt.dayofweek
    v["is_peak"] = v["hour_of_day"].isin(PEAK_HOURS).astype(int)
    return v


VELOCITY_COLUMNS = ["sku_id", "hour", "units", "hour_of_day", "day_of_week", "is_peak"]


def get_velocity(sku_id: str | None = None, since: datetime | None = None, until: datetime | None = None,
                 store_id: str | None = None, open_only: bool = True) -> pd.DataFrame:
    """Dense hourly sales velocity read from the feature store (the Task 2 contract).

    Columns: sku_id, hour, units, hour_of_day, day_of_week, is_peak -- one row per
    (SKU, hour) with explicit zeros for hours without sales. `since` is inclusive, `until`
    exclusive; by default the frame runs from the first recorded hour to the *latest hour
    any SKU sold in*, so a SKU that went silent shows a trailing run of zeros (that tail is
    exactly the phantom-void signal). `sku_id=None` returns every catalog SKU, including ones
    that never sold. `open_only` drops hours when the store is closed (OPEN_HOUR-CLOSE_HOUR),
    which are structural zeros and would otherwise pollute the ZIP baseline.
    """
    sparse = store.list_hourly_velocity(store_id=store_id, sku_id=sku_id, since=since, until=until)
    last = store.latest_velocity_hour(store_id)
    if not sparse or last is None:
        return pd.DataFrame({c: pd.Series(dtype="datetime64[ns]" if c == "hour" else "object" if c == "sku_id" else "int64")
                             for c in VELOCITY_COLUMNS})
    start = pd.Timestamp(since).floor("h") if since else pd.Timestamp(min(r["hour"] for r in sparse))
    end = (pd.Timestamp(until).floor("h") - pd.Timedelta(hours=1)) if until else pd.Timestamp(last)
    hours = pd.date_range(start, end, freq="h")
    if open_only:
        hours = hours[(hours.hour >= OPEN_HOUR) & (hours.hour < CLOSE_HOUR)]
    sku_ids = [sku_id] if sku_id else [s.id for s in store.list_skus()]
    grid = pd.MultiIndex.from_product([sku_ids, hours], names=["sku_id", "hour"]).to_frame(index=False)
    sales = pd.DataFrame(sparse).groupby(["sku_id", "hour"], as_index=False)["units"].sum()
    sales["hour"] = pd.to_datetime(sales["hour"])
    out = grid.merge(sales, on=["sku_id", "hour"], how="left")
    out["units"] = out["units"].fillna(0).astype(int)
    return add_time_features(out)[VELOCITY_COLUMNS]


def hours_since_last_sale(as_of: datetime | None = None, store_id: str | None = None) -> pd.DataFrame:
    """Per SKU: hours since the end of the last hour it sold in, measured to `as_of`.

    Returns [sku_id, last_sale_hour, hours_since_last_sale]. `as_of` defaults to the end of the
    latest data hour. Wall-clock hours (closed hours count), at hourly resolution. A SKU with no
    sales in the data gets last_sale_hour=NaT and the full span of the data as its gap.
    """
    v = get_velocity(store_id=store_id, open_only=False)
    if v.empty:
        return pd.DataFrame({"sku_id": pd.Series(dtype="object"),
                             "last_sale_hour": pd.Series(dtype="datetime64[ns]"),
                             "hours_since_last_sale": pd.Series(dtype="float64")})
    as_of_ts = pd.Timestamp(as_of) if as_of else v["hour"].max() + pd.Timedelta(hours=1)
    first = v["hour"].min()
    last_sale = v[v["units"] > 0].groupby("sku_id")["hour"].max()
    out = pd.DataFrame({"sku_id": v["sku_id"].unique()})
    out["last_sale_hour"] = out["sku_id"].map(last_sale)
    ended = out["last_sale_hour"] + pd.Timedelta(hours=1)
    gap = (as_of_ts - ended.fillna(first)).dt.total_seconds() / 3600
    out["hours_since_last_sale"] = gap.clip(lower=0)
    return out
