"""Time helpers.

POS timestamps are handled as naive *store-clock* times (Sri Lanka, UTC+5:30,
no DST). Timezone-aware input is converted to store time on the way in. When
talking to Postgres we label the store clock as UTC (`to_db`) and strip it
again on the way out (`from_db`), so values round-trip identically whatever
timezone the database session uses.
"""
from datetime import datetime, timedelta, timezone

STORE_TZ = timezone(timedelta(hours=5, minutes=30))


def store_now() -> datetime:
    return datetime.now(STORE_TZ).replace(tzinfo=None)


def to_store_time(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        dt = dt.astimezone(STORE_TZ).replace(tzinfo=None)
    return dt


def floor_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def to_db(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat()


def from_db(value: str | datetime) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
