from datetime import UTC, datetime
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

    updates = []
    for event in events:
        new_category = normalize_category(event, event.get("original_text"))
        if new_category != event.get("category"):
            updates.append((event, new_category))

    print(f"events_checked={len(events)}")
    print(f"category_updates={len(updates)}")

    for event, new_category in updates:
        (
            supabase.table("events")
            .update(
                {
                    "category": new_category,
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            )
            .eq("id", event["id"])
            .execute()
        )
        print(f"{event['id']} | {event['category']} -> {new_category} | {event['title']}")


if __name__ == "__main__":
    main()
