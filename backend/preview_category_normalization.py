import sys

from app.category_normalization import normalize_category
from app.db import get_supabase_client


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,description,venue_name,address,category,original_text,status")
        .in_("status", ["published", "needs_review"])
        .execute()
        .data
        or []
    )

    changes = []
    for event in events:
        new_category = normalize_category(event, event.get("original_text"))
        if new_category != event.get("category"):
            changes.append((event, new_category))

    print(f"events_checked={len(events)}")
    print(f"category_changes={len(changes)}")

    for event, new_category in changes[:80]:
        print("-" * 80)
        print(f"ID: {event['id']}")
        print(f"Title: {event['title']}")
        print(f"Status: {event['status']}")
        print(f"Category: {event.get('category')} -> {new_category}")


if __name__ == "__main__":
    main()
