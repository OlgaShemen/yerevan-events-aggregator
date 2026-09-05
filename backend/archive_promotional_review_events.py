import argparse
import sys
from datetime import UTC, datetime

from app.db import get_supabase_client
from app.event_filtering import is_promotional_event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or archive promotional giveaway cards from the review queue."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Archive matched cards. Without this flag only show a preview.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,description,status")
        .eq("status", "needs_review")
        .execute()
        .data
        or []
    )
    promotional = [event for event in events if is_promotional_event(event)]

    for event in promotional:
        print(f"{event['id']} | {event['title']}")

    if args.apply:
        for event in promotional:
            supabase.table("events").update(
                {"status": "archived", "updated_at": datetime.now(UTC).isoformat()}
            ).eq("id", event["id"]).execute()
            supabase.table("processing_logs").insert(
                {
                    "event_id": event["id"],
                    "step": "archive_promotional_review_event",
                    "status": "success",
                    "message": "Archived promotional giveaway from review queue.",
                    "details": {"reason": "promotional_giveaway"},
                }
            ).execute()

    print(f"matched={len(promotional)} applied={len(promotional) if args.apply else 0}")


if __name__ == "__main__":
    main()
