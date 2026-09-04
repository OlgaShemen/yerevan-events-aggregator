import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


YEREVAN = ZoneInfo("Asia/Yerevan")
RECURRENCE_PATTERN = re.compile(
    r"\b(?:ежедневно|каждый\s+день|кажд(?:ый|ую|ое|ые)\s+"
    r"(?:понедельник|вторник|сред\w*|четверг|пятниц\w*|суббот\w*|воскресень\w*|выходн\w*)|"
    r"по\s+(?:будням|выходным)|daily|every\s+(?:day|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    re.IGNORECASE,
)


def yerevan_today() -> date:
    return datetime.now(YEREVAN).date()


def normalize_schedule(text: str) -> str:
    return " ".join(text.lower().split())


def prepare_recurring_event(event: dict, raw_item: dict) -> dict:
    event = dict(event)
    schedule = (event.get("recurring_schedule") or "").strip()
    event["recurring_schedule"] = None
    event["display_until"] = None
    raw_text = raw_item.get("raw_text") or ""
    if not schedule or not RECURRENCE_PATTERN.search(schedule):
        return event
    if normalize_schedule(schedule) not in normalize_schedule(raw_text):
        return event
    # Explicitly dated events keep their dates; only undated offers use this window.
    if event.get("date_start") or event.get("date_end"):
        return event

    source_date = (raw_item.get("raw_payload") or {}).get("telegram_date")
    if not isinstance(source_date, str):
        return event
    try:
        published = datetime.fromisoformat(source_date.replace("Z", "+00:00"))
        if published.tzinfo is None:
            return event
        published_day = published.astimezone(YEREVAN).date()
    except ValueError:
        return event

    if published_day > yerevan_today():
        return event
    event["recurring_schedule"] = schedule
    event["display_until"] = (published_day + timedelta(days=6 - published_day.weekday())).isoformat()
    return event


def recurring_event_expired(event: dict, today: date | None = None) -> bool:
    until = event.get("display_until")
    return bool(until and until < (today or yerevan_today()).isoformat())
