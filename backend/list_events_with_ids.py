import sys

from app.db import get_supabase_client


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,date_start,date_end,time_start,time_end,venue_name,status,confidence_score")
        .order("date_start")
        .execute()
        .data
    )

    if not events:
        print("No events found.")
        return

    for event in events:
        print("-" * 80)
        print(f"ID: {event['id']}")
        print(f"Title: {event['title']}")
        print(f"Date: {event['date_start']} - {event['date_end']}")
        print(f"Time: {event['time_start']} - {event['time_end']}")
        print(f"Venue: {event['venue_name']}")
        print(f"Status: {event['status']}")
        print(f"Confidence: {event['confidence_score']}")


if __name__ == "__main__":
    main()
