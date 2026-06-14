import argparse
from datetime import UTC, datetime
import sys

from app.db import get_supabase_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge a duplicate event into a primary event.")
    parser.add_argument("--primary-id", required=True, help="Event ID to keep.")
    parser.add_argument("--duplicate-id", required=True, help="Event ID to archive.")
    return parser.parse_args()


def get_event(supabase, event_id: str) -> dict:
    response = (
        supabase.table("events")
        .select("id,title,status")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise RuntimeError(f"Event not found: {event_id}")

    return response.data[0]


def copy_event_sources(supabase, primary_id: str, duplicate_id: str) -> int:
    duplicate_sources = (
        supabase.table("event_sources")
        .select("raw_item_id,source_id,source_url")
        .eq("event_id", duplicate_id)
        .execute()
        .data
    )

    copied = 0

    for source in duplicate_sources or []:
        existing = (
            supabase.table("event_sources")
            .select("id")
            .eq("event_id", primary_id)
            .eq("raw_item_id", source["raw_item_id"])
            .limit(1)
            .execute()
        )

        if existing.data:
            continue

        supabase.table("event_sources").insert(
            {
                "event_id": primary_id,
                "raw_item_id": source["raw_item_id"],
                "source_id": source["source_id"],
                "source_url": source["source_url"],
                "is_primary": False,
            }
        ).execute()
        copied += 1

    return copied


def write_log(supabase, primary: dict, duplicate: dict, copied_sources: int) -> None:
    supabase.table("processing_logs").insert(
        {
            "event_id": primary["id"],
            "step": "manual_duplicate_merge",
            "status": "success",
            "message": "Duplicate event was merged manually.",
            "details": {
                "primary_id": primary["id"],
                "primary_title": primary["title"],
                "duplicate_id": duplicate["id"],
                "duplicate_title": duplicate["title"],
                "copied_sources": copied_sources,
            },
        }
    ).execute()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    if args.primary_id == args.duplicate_id:
        raise RuntimeError("Primary and duplicate IDs must be different.")

    supabase = get_supabase_client()
    primary = get_event(supabase, args.primary_id)
    duplicate = get_event(supabase, args.duplicate_id)

    copied_sources = copy_event_sources(supabase, primary["id"], duplicate["id"])

    supabase.table("events").update(
        {
            "status": "archived",
            "updated_at": datetime.now(UTC).isoformat(),
        }
    ).eq("id", duplicate["id"]).execute()

    write_log(supabase, primary, duplicate, copied_sources)

    print(f"Kept primary event: {primary['title']}")
    print(f"Archived duplicate event: {duplicate['title']}")
    print(f"Copied sources: {copied_sources}")


if __name__ == "__main__":
    main()
