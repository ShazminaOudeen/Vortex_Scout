"""Aggregate raw POS rows into hourly sales velocity per SKU."""
import pandas as pd


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
    v["is_peak"] = v["hour_of_day"].isin([11, 12, 18, 19, 20]).astype(int)
    return v
