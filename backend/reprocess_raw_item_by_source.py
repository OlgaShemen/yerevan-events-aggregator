import argparse
import sys

from app.db import get_supabase_client
from process_raw_item_to_event import process_raw_item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reprocess one raw_item by source_url, even if it is already processed."
    )
    parser.add_argument("--source-url", required=True)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    supabase = get_supabase_client()
    raw_items = (
        supabase.table("raw_items")
        .select("id,source_id,source_url,raw_text,status")
        .eq("source_url", args.source_url)
        .execute()
        .data
        or []
    )

    if not raw_items:
        raise RuntimeError(f"Raw item not found: {args.source_url}")

    if len(raw_items) > 1:
        raise RuntimeError(f"Expected one raw item, found {len(raw_items)}.")

    result = process_raw_item(supabase, raw_items[0])
    print(f"raw_item={result['raw_item_id']}")
    print(f"action={result['action']}")
    print(f"event_ids={','.join(result.get('event_ids') or []) or None}")
    print(f"event_statuses={','.join(result.get('event_statuses') or []) or None}")
    print(f"saved_count={result.get('saved_count', 0)}")


if __name__ == "__main__":
    main()
