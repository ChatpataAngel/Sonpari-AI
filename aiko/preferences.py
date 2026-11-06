"""Validation helpers for per-user language, time zone and quiet-hour preferences."""
from __future__ import annotations
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LANGUAGES = {"en", "hi", "hinglish", "auto"}


def validate_timezone(value: str) -> str:
    value = (value or "").strip()
    if not value or len(value) > 80 or ".." in value:
        raise ValueError("Use an IANA time zone such as Asia/Kolkata or Europe/London.")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise ValueError("Unknown time zone. Use an IANA name such as Asia/Kolkata.")
    return value


def parse_quiet_hours(value: str) -> tuple[int | None, int | None]:
    value = (value or "").strip().lower()
    if value in {"off", "none", "disable", "disabled"}:
        return None, None
    match = re.fullmatch(r"\s*(\d{1,2})\s*[-–]\s*(\d{1,2})\s*", value)
    if not match:
        raise ValueError("Use /prefs quiet 23-08, or /prefs quiet off to disable quiet hours.")
    start, end = map(int, match.groups())
    if not (0 <= start <= 23 and 0 <= end <= 23) or start == end:
        raise ValueError("Quiet hours must use different whole hours between 00 and 23.")
    return start, end


def quiet_now(hour: int, start: int | None, end: int | None) -> bool:
    if start is None or end is None:
        return False
    return (start <= hour < end) if start < end else (hour >= start or hour < end)
