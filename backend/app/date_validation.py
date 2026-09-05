import re
from datetime import datetime, timedelta, timezone


YEREVAN_TIMEZONE = timezone(timedelta(hours=4))


WEEKDAY_PATTERN = re.compile(
    r"\b("
    r"понедельник\w*|вторник\w*|сред\w*|четверг\w*|пятниц\w*|"
    r"суббот\w*|воскресень\w*|"
    r"пн|вт|ср|чт|пт|сб|вск|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r")\b",
    re.IGNORECASE,
)

CONCRETE_DATE_PATTERN = re.compile(
    r"("
    r"\b\d{1,2}[./-]\d{1,2}\b|"
    r"\b\d{1,2}\s*(?:"
    r"январ[яь]|феврал[яь]|март[а]?|апрел[яь]|ма[яй]|июн[яь]|"
    r"июл[яь]|август[а]?|сентябр[яь]|октябр[яь]|ноябр[яь]|декабр[яь]|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
    r")\b"
    r"|\b(?:"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
    r")\s+\d{1,2}(?:st|nd|rd|th)?\b"
    r")",
    re.IGNORECASE,
)

EXPLICIT_RELATIVE_DATE_PATTERN = re.compile(
    r"\b(?:сегодня|завтра|послезавтра|today|tomorrow|day\s+after\s+tomorrow)\b|"
    r"\b(?:эт(?:от|у|о)|следующ(?:ий|ую|ее))\s+"
    r"(?:понедельник|вторник|сред\w*|четверг|пятниц\w*|суббот\w*|воскресень\w*)\b|"
    r"\b(?:this|next)\s+"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)


def telegram_publication_date(published_at: str | None) -> str | None:
    if not published_at:
        return None
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if published.tzinfo is None:
        return None
    return published.astimezone(YEREVAN_TIMEZONE).date().isoformat()


def has_weekday_without_concrete_date(raw_text: str | None) -> bool:
    if not raw_text:
        return False

    return (
        bool(WEEKDAY_PATTERN.search(raw_text))
        and not bool(CONCRETE_DATE_PATTERN.search(raw_text))
        and not bool(EXPLICIT_RELATIVE_DATE_PATTERN.search(raw_text))
    )


def clear_inferred_weekday_dates(event: dict, raw_text: str | None) -> dict:
    if has_weekday_without_concrete_date(raw_text):
        event["date_start"] = None
        event["date_end"] = None

    return event
