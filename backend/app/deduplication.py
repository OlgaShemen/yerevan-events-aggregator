from dataclasses import dataclass
from difflib import SequenceMatcher
import re


TITLE_THRESHOLD = 0.72
VENUE_THRESHOLD = 0.82
TIME_THRESHOLD_MINUTES = 30
TITLE_OVERLAP_THRESHOLD = 0.5

STOP_WORDS = {
    "для",
    "или",
    "как",
    "концерт",
    "представление",
    "спектакль",
    "мероприятие",
    "вечер",
    "детей",
    "взрослых",
}


@dataclass(frozen=True)
class DuplicateCandidate:
    event_a: dict
    event_b: dict
    title_similarity: float
    venue_similarity: float
    score: float
    reason: str


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    normalized = value.casefold()
    normalized = re.sub(r"https?://\S+", " ", normalized)
    normalized = re.sub(r"[^\w\s]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def meaningful_tokens(value: str | None) -> set[str]:
    return {
        token
        for token in normalize_text(value).split()
        if len(token) >= 4 and token not in STOP_WORDS
    }


def similarity(left: str | None, right: str | None) -> float:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)

    if not left_normalized or not right_normalized:
        return 0.0

    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def token_overlap(left: str | None, right: str | None) -> float:
    left_tokens = meaningful_tokens(left)
    right_tokens = meaningful_tokens(right)

    if not left_tokens or not right_tokens:
        return 0.0

    return len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))


def contains_normalized_title(left: str | None, right: str | None) -> bool:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)

    if len(left_normalized) < 8 or len(right_normalized) < 8:
        return False

    return left_normalized in right_normalized or right_normalized in left_normalized


def minutes_from_time(value: str | None) -> int | None:
    if not value:
        return None

    parts = value.split(":")
    if len(parts) < 2:
        return None

    try:
        return (int(parts[0]) * 60) + int(parts[1])
    except ValueError:
        return None


def same_or_close_time(event_a: dict, event_b: dict) -> bool:
    time_a = minutes_from_time(event_a.get("time_start"))
    time_b = minutes_from_time(event_b.get("time_start"))

    if time_a is None or time_b is None:
        return True

    return abs(time_a - time_b) <= TIME_THRESHOLD_MINUTES


def same_date(event_a: dict, event_b: dict) -> bool:
    date_a = event_a.get("date_start")
    date_b = event_b.get("date_start")
    return bool(date_a and date_b and date_a == date_b)


def same_or_missing_venue(event_a: dict, event_b: dict) -> bool:
    venue_score = similarity(event_a.get("venue_name"), event_b.get("venue_name"))

    if not event_a.get("venue_name") or not event_b.get("venue_name"):
        return True

    return venue_score >= VENUE_THRESHOLD


def duplicate_reason(event_a: dict, event_b: dict) -> DuplicateCandidate | None:
    if not same_date(event_a, event_b):
        return None

    if not same_or_close_time(event_a, event_b):
        return None

    title_score = similarity(event_a.get("title"), event_b.get("title"))
    venue_score = similarity(event_a.get("venue_name"), event_b.get("venue_name"))

    venue_matches = same_or_missing_venue(event_a, event_b)

    if title_score >= 0.9:
        score = (title_score * 0.75) + (venue_score * 0.25)
        return DuplicateCandidate(
            event_a=event_a,
            event_b=event_b,
            title_similarity=title_score,
            venue_similarity=venue_score,
            score=score,
            reason="same date and very similar title",
        )

    if title_score >= TITLE_THRESHOLD and venue_matches:
        score = (title_score * 0.65) + (venue_score * 0.35)
        return DuplicateCandidate(
            event_a=event_a,
            event_b=event_b,
            title_similarity=title_score,
            venue_similarity=venue_score,
            score=score,
            reason="same date, similar title, same or missing venue",
        )

    overlap_score = token_overlap(event_a.get("title"), event_b.get("title"))
    if venue_matches and (
        overlap_score >= TITLE_OVERLAP_THRESHOLD
        or contains_normalized_title(event_a.get("title"), event_b.get("title"))
    ):
        score = (overlap_score * 0.55) + (venue_score * 0.45)
        return DuplicateCandidate(
            event_a=event_a,
            event_b=event_b,
            title_similarity=title_score,
            venue_similarity=venue_score,
            score=score,
            reason="same date/time/place and overlapping title words",
        )

    return None


def find_duplicate_candidates(events: list[dict]) -> list[DuplicateCandidate]:
    candidates = []

    for index, event_a in enumerate(events):
        for event_b in events[index + 1 :]:
            candidate = duplicate_reason(event_a, event_b)
            if candidate:
                candidates.append(candidate)

    return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)
