import argparse
import sys

from app.db import get_supabase_client
from app.venue_resolution import resolve_known_venue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or apply trusted venue context to review events."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write resolved venue fields. Without this flag only show a preview.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,status,venue_name,address,original_text")
        .eq("status", "needs_review")
        .execute()
        .data
        or []
    )

    changes = []
    for event in events:
        resolved = resolve_known_venue(event, event.get("original_text"))
        updates = {
            field: resolved.get(field)
            for field in ("venue_name", "address")
            if resolved.get(field) != event.get(field)
        }
        if not updates:
            continue
        changes.append((event, updates))
        print(f"{event['id']} | {event['title']} | {updates}")

    if args.apply:
        for event, updates in changes:
            supabase.table("events").update(updates).eq("id", event["id"]).execute()
            supabase.table("processing_logs").insert(
                {
                    "event_id": event["id"],
                    "step": "backfill_known_venue",
                    "status": "success",
                    "message": "Venue restored from trusted shared context.",
                    "details": {"updates": updates},
                }
            ).execute()

    print(f"matched={len(changes)} applied={len(changes) if args.apply else 0}")


if __name__ == "__main__":
    main()
