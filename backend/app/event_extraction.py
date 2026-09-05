import json
from datetime import datetime

from app.config import get_settings
from app.date_validation import YEREVAN_TIMEZONE, telegram_publication_date
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
        "recurring_schedule": {"type": ["string", "null"]},
        "venue_name": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]},
        "category": {
            "type": "string",
            "enum": [
                "concert",
                "theatre",
                "exhibition",
                "lecture",
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
        "recurring_schedule",
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


def extract_event_from_text(
    raw_text: str,
    source_url: str | None = None,
    published_at: str | None = None,
) -> dict:
    settings = get_settings()
    client = get_openai_client()
    current_date = datetime.now(YEREVAN_TIMEZONE).date().isoformat()
    source_date = telegram_publication_date(published_at)
    source_date_instruction = (
        f"The Telegram source post was published on {source_date} in Asia/Yerevan. "
        "Use that publication date only to resolve an explicit relative date such as today, tomorrow, "
        "the day after tomorrow, this Sunday, or next Sunday, and to infer the year of an explicit "
        "month-and-day date. Never use the publication date as the event date when the announcement "
        "contains no explicit calendar or relative date. "
        if source_date
        else "The Telegram source publication date is unavailable. Do not calculate relative dates. "
    )

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {
                "role": "system",
                "content": (
                    "You classify and extract event information from raw announcements in Yerevan. "
                    "Return only fields that match the provided JSON schema. "
                    f"The current date is {current_date}. "
                    + source_date_instruction
                    + "If the source publication date is unavailable, use the current date to infer the year "
                    "only for an explicit month-and-day date. "
                    "Do not convert weekdays into calendar dates. If the text says only Monday, Tuesday, "
                    "this week, every Tuesday, or similar recurring weekday wording without a concrete calendar date, "
                    "set date_start and date_end to null. "
                    "Never calculate dates from phrases like 'this week', 'next week', 'Monday', 'Tuesday', "
                    "'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Понедельник', 'Вторник', "
                    "'Среда', 'Четверг', 'Пятница', 'Суббота', or 'Воскресенье'. "
                    "The only exception is when the same event explicitly says today, tomorrow, the day after "
                    "tomorrow, this weekday, or next weekday and a source publication date is available. "
                    "Examples: 'Понедельник: 11:00 Yoga' means date_start=null and time_start=11:00. "
                    "'Расписание занятий на эту неделю' means date_start=null unless each item has a concrete "
                    "calendar date such as '12 июня', '12.06', or 'June 12'. "
                    "Set is_event to false and return an empty events array if the text is not a real offline or online event announcement. "
                    "For an offer with explicit recurring wording (daily, every Saturday, etc.) but no concrete calendar dates, "
                    "keep date_start and date_end null and set recurring_schedule to an exact contiguous quote from this "
                    "event's source text containing the recurrence wording AND all its time slots. Preserve line breaks. "
                    "Keep one event for the same recurring activity with multiple daily groups, not one event per group or day. "
                    "For example, daily SUP tours with 09:00-15:00 and 16:00-22:00 groups form one event. "
                    "Plain missing dates, 'this week', 'summer', and a weekday alone do not establish recurrence. "
                    "For those cases and for explicitly dated events, set recurring_schedule to null. "
                    "Do not borrow recurrence wording from another event in a digest. "
                    "Use category lecture for lectures, lecture series, public talks, and educational talks. "
                    "Do not use lecture for workshops, discussions after a film, theatre performances, or quizzes. "
                    "If is_event is false, explain why in rejection_reason. "
                    "Exclude commercial promotions, promotional contests, giveaways, prize draws, referral campaigns, "
                    "cashback offers, and gifts conditional on purchases, money transfers, subscriptions, likes, "
                    "or reposts. These are advertising offers, not events, even if they have a deadline or a draw date. "
                    "For example, 'KWIKPAY promotion: Apple gifts for transfers to Armenia' is not an event. "
                    "In a mixed digest, omit only promotional offers and keep genuine events. "
                    "Keep actual cultural, creative, and sports competitions, quizzes, tournaments, and charity events; "
                    "prizes, sponsors, or the word 'contest' alone do not make an event a promotional giveaway. "
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
