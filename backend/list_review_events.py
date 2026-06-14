import sys

from app.db import get_supabase_client


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select(
            "id,title,date_start,time_start,venue_name,address,category,language,"
            "price_text,status,confidence_score,source_url"
        )
        .eq("status", "needs_review")
        .order("created_at")
        .execute()
        .data
    )

    if not events:
        print("No events with status=needs_review found.")
        return

    for event in events:
        print("-" * 80)
        print(f"ID: {event['id']}")
        print(f"Title: {event['title']}")
        print(f"Date: {event['date_start']} {event['time_start'] or ''}".strip())
        print(f"Venue: {event['venue_name']}")
        print(f"Address: {event['address']}")
        print(f"Category: {event['category']}")
        print(f"Language: {event['language']}")
        print(f"Price: {event['price_text']}")
        print(f"Confidence: {event['confidence_score']}")
        print(f"Source: {event['source_url']}")


if __name__ == "__main__":
    main()
