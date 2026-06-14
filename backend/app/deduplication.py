from dataclasses import dataclass
from difflib import SequenceMatcher
import re


TITLE_THRESHOLD = 0.72
VENUE_THRESHOLD = 0.82


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


def similarity(left: str | None, right: str | None) -> float:
    left_normalized = normalize_text(left)
    right_normalized = normalize_text(right)

    if not left_normalized or not right_normalized:
        return 0.0

    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def same_date(event_a: dict, event_b: dict) -> bool:
    date_a = event_a.get("date_start")
    date_b = event_b.get("date_start")
    return bool(date_a and date_b and date_a == date_b)


def duplicate_reason(event_a: dict, event_b: dict) -> DuplicateCandidate | None:
    if not same_date(event_a, event_b):
        return None

    title_score = similarity(event_a.get("title"), event_b.get("title"))
    venue_score = similarity(event_a.get("venue_name"), event_b.get("venue_name"))

    same_or_missing_venue = venue_score >= VENUE_THRESHOLD
    if not event_a.get("venue_name") or not event_b.get("venue_name"):
        same_or_missing_venue = True

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

    if title_score >= TITLE_THRESHOLD and same_or_missing_venue:
        score = (title_score * 0.65) + (venue_score * 0.35)
        return DuplicateCandidate(
            event_a=event_a,
            event_b=event_b,
            title_similarity=title_score,
            venue_similarity=venue_score,
            score=score,
            reason="same date, similar title, same or missing venue",
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
