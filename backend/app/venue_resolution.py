from dataclasses import dataclass
import re


@dataclass(frozen=True)
class KnownVenue:
    name: str
    address: str | None
    venue_alias: re.Pattern
    shared_context: re.Pattern


KNOWN_VENUES = (
    KnownVenue(
        name="Ari Standup Club",
        address="ул. Вардананц, 18/1",
        venue_alias=re.compile(r"\bari\s+standup(?:\s+club)?\b|ари\s+стендап", re.IGNORECASE),
        shared_context=re.compile(
            r"расписани\w*\s+на\s+недел\w*[\s\S]*aristandupclub\.am",
            re.IGNORECASE,
        ),
    ),
    KnownVenue(
        name="Бар «Муха»",
        address=None,
        venue_alias=re.compile(r"(?:бар\w*\s+)?[«\"]?мух[аеуы][»\"]?|\bmuha\b", re.IGNORECASE),
        shared_context=re.compile(r"\bдвиж\s+в\s+мухе\b", re.IGNORECASE),
    ),
    KnownVenue(
        name="Ереван глазами инженера",
        address="Уточните у организатора",
        venue_alias=re.compile(r"\bереван\s+глазами\s+инженера\b", re.IGNORECASE),
        shared_context=re.compile(r"\bереван\s+глазами\s+инженера\b", re.IGNORECASE),
    ),
)


def resolve_known_venue(event: dict, raw_text: str | None) -> dict:
    event = dict(event)
    current_name = (event.get("venue_name") or "").strip()
    text = raw_text or ""

    if current_name:
        matches = [venue for venue in KNOWN_VENUES if venue.venue_alias.search(current_name)]
    else:
        matches = [venue for venue in KNOWN_VENUES if venue.shared_context.search(text)]

    if len(matches) != 1:
        return event

    venue = matches[0]
    if not current_name:
        event["venue_name"] = venue.name
    if not event.get("address") and venue.address:
        event["address"] = venue.address
    event["venue_resolution"] = "trusted_directory"
    return event
