from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def to_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def to_utc_iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = to_utc_naive(value)
    if normalized is None:
        return None
    return normalized.isoformat(timespec="milliseconds") + "Z"
