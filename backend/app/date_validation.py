import re


WEEKDAY_PATTERN = re.compile(
    r"\b("
    r"понедельник|вторник|среда|четверг|пятница|суббота|воскресенье|"
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
    r"jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|sept|oct|nov|dec"
    r")\b"
    r")",
    re.IGNORECASE,
)


def has_weekday_without_concrete_date(raw_text: str | None) -> bool:
    if not raw_text:
        return False

    return bool(WEEKDAY_PATTERN.search(raw_text)) and not bool(
        CONCRETE_DATE_PATTERN.search(raw_text)
    )


def clear_inferred_weekday_dates(event: dict, raw_text: str | None) -> dict:
    if has_weekday_without_concrete_date(raw_text):
        event["date_start"] = None
        event["date_end"] = None

    return event
