import argparse
import sys

from app.db import get_supabase_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show raw source text for an event.")
    parser.add_argument("--event-id", required=True)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()

    event = (
        supabase.table("events")
        .select("id,title")
        .eq("id", args.event_id)
        .limit(1)
        .execute()
        .data
    )

    if not event:
        raise RuntimeError(f"Event not found: {args.event_id}")

    raw_links = (
        supabase.table("event_sources")
        .select("raw_item_id,source_url")
        .eq("event_id", args.event_id)
        .execute()
        .data
    )

    print(f"Event: {event[0]['title']}")

    for link in raw_links or []:
        raw_item = (
            supabase.table("raw_items")
            .select("raw_text")
            .eq("id", link["raw_item_id"])
            .limit(1)
            .execute()
            .data
        )

        print("-" * 80)
        print(f"Source: {link['source_url']}")
        print(raw_item[0]["raw_text"] if raw_item else "Raw item not found.")


if __name__ == "__main__":
    main()
