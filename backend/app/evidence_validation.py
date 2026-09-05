import re


EVIDENCE_VERSION = 1
EVIDENCE_FIELDS = {
    "date": "date_evidence",
    "time": "time_evidence",
    "place": "venue_evidence",
}


def normalize_for_evidence(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip().casefold()


def quote_exists_in_source(quote: str, raw_text: str | None) -> bool:
    normalized_quote = normalize_for_evidence(quote)
    normalized_source = normalize_for_evidence(raw_text)
    return bool(normalized_quote and normalized_quote in normalized_source)


def clean_quotes(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [quote.strip() for quote in value if isinstance(quote, str) and quote.strip()]


def validate_event_evidence(event: dict, raw_text: str | None) -> dict:
    event = dict(event)
    requirements = {
        "date": bool(event.get("date_start") or event.get("date_end")),
        "time": bool(event.get("time_start") or event.get("time_end")),
        "place": bool(event.get("venue_name") or event.get("address")),
    }
    validation = {"version": EVIDENCE_VERSION}

    for evidence_type, field_name in EVIDENCE_FIELDS.items():
        required = requirements[evidence_type]
        quotes = clean_quotes(event.get(field_name))
        valid_quotes = [quote for quote in quotes if quote_exists_in_source(quote, raw_text)]
        trusted = evidence_type == "place" and event.get("venue_resolution") == "trusted_directory"
        confirmed = not required or trusted or bool(quotes and len(valid_quotes) == len(quotes))
        validation[evidence_type] = {
            "required": required,
            "confirmed": confirmed,
            "quotes": valid_quotes,
            "invalid_quotes": [quote for quote in quotes if quote not in valid_quotes],
            "method": "trusted_directory" if trusted else "source_quote",
        }

    event["evidence_validation"] = validation
    return event
