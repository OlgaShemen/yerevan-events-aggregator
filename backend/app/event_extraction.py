import json
from datetime import date

from app.config import get_settings
from app.openai_client import get_openai_client


EVENT_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {"type": ["string", "null"]},
        "date_start": {"type": ["string", "null"]},
        "time_start": {"type": ["string", "null"]},
        "date_end": {"type": ["string", "null"]},
        "time_end": {"type": ["string", "null"]},
        "venue_name": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "category": {
            "type": "string",
            "enum": [
                "concert",
                "theatre",
                "exhibition",
                "party",
                "movie",
                "workshop",
                "tourism",
                "food",
                "kids",
                "other",
            ],
        },
        "description": {"type": ["string", "null"]},
        "language": {
            "type": "string",
            "enum": ["hy", "ru", "en", "mixed", "unknown"],
        },
        "price_text": {"type": ["string", "null"]},
        "source_url": {"type": ["string", "null"]},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "title",
        "date_start",
        "time_start",
        "date_end",
        "time_end",
        "venue_name",
        "address",
        "category",
        "description",
        "language",
        "price_text",
        "source_url",
        "confidence_score",
    ],
}

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "is_event": {"type": "boolean"},
        "rejection_reason": {"type": ["string", "null"]},
        "events": {
            "type": "array",
            "items": EVENT_ITEM_SCHEMA,
        },
    },
    "required": [
        "is_event",
        "rejection_reason",
        "events",
    ],
}


def extract_event_from_text(raw_text: str, source_url: str | None = None) -> dict:
    settings = get_settings()
    client = get_openai_client()
    current_date = date.today().isoformat()

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You classify and extract event information from raw announcements in Yerevan. "
                    "Return only fields that match the provided JSON schema. "
                    f"The current date is {current_date}. "
                    "Use this current date to infer the year when the announcement gives dates without a year. "
                    "If a date without a year has already passed in the current year, use the next year only when "
                    "the text clearly describes an upcoming event. "
                    "Do not convert weekdays into calendar dates. If the text says only Monday, Tuesday, "
                    "this week, every Tuesday, or similar recurring weekday wording without a concrete calendar date, "
                    "set date_start and date_end to null. "
                    "Never calculate dates from phrases like 'this week', 'next week', 'Monday', 'Tuesday', "
                    "'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Понедельник', 'Вторник', "
                    "'Среда', 'Четверг', 'Пятница', 'Суббота', or 'Воскресенье'. "
                    "Examples: 'Понедельник: 11:00 Yoga' means date_start=null and time_start=11:00. "
                    "'Расписание занятий на эту неделю' means date_start=null unless each item has a concrete "
                    "calendar date such as '12 июня', '12.06', or 'June 12'. "
                    "Set is_event to false and return an empty events array if the text is not a real offline or online event announcement. "
                    "If is_event is false, explain why in rejection_reason. "
                    "If one post contains a schedule, digest, weekly program, or several separate announcements, "
                    "extract each separate event as a separate item in the events array. "
                    "For schedules, digests, and weekly programs, do not create a generic summary event "
                    "such as 'week at venue', 'program of events', or 'schedule' when you can extract "
                    "the individual listed events instead. "
                    "If one event has several dates, shifts, or sessions, keep it as one event and use the earliest "
                    "clear date as date_start and the latest clear date as date_end. "
                    "Use null when a field is missing. Dates must use YYYY-MM-DD. "
                    "Times must use HH:MM in 24-hour format. "
                    "Do not invent details that are not present in the text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Source URL: {source_url or 'unknown'}\n\n"
                    f"Raw event text:\n{raw_text}"
                ),
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "event_extraction",
                "schema": EXTRACTION_SCHEMA,
                "strict": True,
            }
        },
    )

    return json.loads(response.output_text)
