"""Human-friendly text form of a weekly schedule.

A day is written as comma-separated comfort periods, each ``HH:MM-HH:MM`` on a
30-minute grid, e.g. ``06:00-08:30, 16:30-22:30`` (max 3). An ``end`` of
``00:00`` means end-of-day. An empty string clears the day.

Shared by the ``set_schedule`` service and the Configure (options) dialog so
both accept and render the exact same format.
"""

from __future__ import annotations

from .etrv.properties import DaySchedule

# Ordered Mon..Sun for display; values are the device's day index (0=Sun..6=Sat).
DAY_TO_INDEX: dict[str, int] = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 0,
}

_SLOTS = (("p1_start", "p1_end"), ("p2_start", "p2_end"), ("p3_start", "p3_end"))


def _to_minutes(value: str, *, is_end: bool) -> int:
    value = value.strip()
    try:
        hh, mm = value.split(":")
        minutes = int(hh) * 60 + int(mm)
    except ValueError as exc:
        raise ValueError(f"invalid time '{value}', expected HH:MM") from exc
    if is_end and minutes == 0:
        return 1440  # 00:00 as an end means end-of-day
    return minutes


def _format_minutes(minutes: int) -> str:
    if minutes == 1440:
        return "00:00"
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_day(text: str) -> DaySchedule:
    """Parse a day string into a validated :class:`DaySchedule`."""
    day = DaySchedule()
    chunks = [c.strip() for c in text.split(",") if c.strip()]
    if len(chunks) > 3:
        raise ValueError("at most 3 periods per day")
    for (start_attr, end_attr), chunk in zip(_SLOTS, chunks):
        start, sep, end = chunk.partition("-")
        if not sep:
            raise ValueError(f"period '{chunk}' must look like 06:00-08:30")
        setattr(day, start_attr, _to_minutes(start, is_end=False))
        setattr(day, end_attr, _to_minutes(end, is_end=True))
    day.validate()  # raise early with a clear message before we hit BLE
    return day


def format_day(day: DaySchedule) -> str:
    """Render a :class:`DaySchedule` back to its text form (for prefilling forms)."""
    parts = []
    for start_attr, end_attr in _SLOTS:
        start = getattr(day, start_attr)
        end = getattr(day, end_attr)
        if start == 0 and end == 0:
            continue  # unused period
        parts.append(f"{_format_minutes(start)}-{_format_minutes(end)}")
    return ", ".join(parts)
