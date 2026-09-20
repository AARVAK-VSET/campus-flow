from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current time as an aware UTC datetime (unlike the naive, deprecated datetime.utcnow())."""
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """Return `value` as an aware UTC datetime.

    A naive value is taken to already be UTC (that is what datetime.utcnow() produced for
    every existing row); an aware value is converted, never just stripped of its offset.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
