from app.db import get_supabase_client
import sys


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("title,date_start,venue_name,status,confidence_score")
        .order("created_at")
        .execute()
        .data
    )

    if not events:
        print("No events found.")
        return

    for event in events:
        print(
            f"{event['date_start']} | "
            f"{event['title']} | "
            f"{event['venue_name']} | "
            f"{event['status']} | "
            f"{event['confidence_score']}"
        )


if __name__ == "__main__":
    main()
