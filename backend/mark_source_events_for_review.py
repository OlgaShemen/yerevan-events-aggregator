import argparse
import sys

from app.db import get_supabase_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move all events from one source URL to needs_review."
    )
    parser.add_argument("--source-url", required=True)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()

    events = (
        supabase.table("events")
        .select("id,title,status")
        .eq("source_url", args.source_url)
        .execute()
        .data
        or []
    )

    if not events:
        print("No events found.")
        return

    event_ids = [event["id"] for event in events]

    print(f"found={len(events)}")
    for event in events:
        print(f"{event['status']} | {event['title']}")

    (
        supabase.table("events")
        .update({"status": "needs_review"})
        .in_("id", event_ids)
        .execute()
    )

    print(f"updated={len(event_ids)}")


if __name__ == "__main__":
    main()
