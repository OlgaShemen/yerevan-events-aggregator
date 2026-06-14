import sys

from app.db import get_supabase_client
from app.deduplication import find_duplicate_candidates


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,date_start,venue_name,status,source_url")
        .in_("status", ["published", "needs_review"])
        .order("date_start")
        .execute()
        .data
    )

    candidates = find_duplicate_candidates(events or [])

    if not candidates:
        print("No duplicate candidates found.")
        return

    print(f"Duplicate candidates found: {len(candidates)}")

    for candidate in candidates:
        event_a = candidate.event_a
        event_b = candidate.event_b
        print("-" * 80)
        print(f"Score: {candidate.score:.2f}")
        print(f"Reason: {candidate.reason}")
        print(f"Title similarity: {candidate.title_similarity:.2f}")
        print(f"Venue similarity: {candidate.venue_similarity:.2f}")
        print()
        print(f"A ID: {event_a['id']}")
        print(f"A: {event_a['date_start']} | {event_a['title']} | {event_a['venue_name']} | {event_a['status']}")
        print(f"A source: {event_a['source_url']}")
        print()
        print(f"B ID: {event_b['id']}")
        print(f"B: {event_b['date_start']} | {event_b['title']} | {event_b['venue_name']} | {event_b['status']}")
        print(f"B source: {event_b['source_url']}")


if __name__ == "__main__":
    main()
