from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


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


class UTCDateTime(TypeDecorator):
    """A timezone-aware UTC datetime column that behaves the same on every dialect.

    SQLite ignores tzinfo: it stores an aware value's wall clock with the offset dropped and
    always returns naive values. Normalising here keeps the stored value UTC and hands the
    application aware UTC datetimes. The SQLite column stays DATETIME in the same string
    format, so existing rows are read as UTC and need no migration.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else as_utc(value)

    def process_result_value(self, value, dialect):
        return None if value is None else as_utc(value)
