import argparse
import asyncio
import sys

from app.db import get_supabase_client
from app.deduplication import find_duplicate_candidates
from app.telegram_ingestion import ingest_telegram_posts
from batch_process_raw_items import get_raw_items
from process_raw_item_to_event import process_raw_item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MVP ingestion pipeline.")
    parser.add_argument(
        "--skip-telegram",
        action="store_true",
        help="Do not read Telegram channels; only process existing raw_items.",
    )
    parser.add_argument(
        "--process-limit",
        type=int,
        default=10,
        help="Maximum number of raw_items to process with OpenAI.",
    )
    parser.add_argument(
        "--skip-dedup-check",
        action="store_true",
        help="Do not run duplicate candidate detection.",
    )
    return parser.parse_args()


def process_raw_items(limit: int) -> dict:
    supabase = get_supabase_client()
    raw_items = get_raw_items(supabase, limit)

    result = {
        "saved": 0,
        "ignored": 0,
        "failed": 0,
    }

    if not raw_items:
        print("No raw items with status=new found.")
        return result

    for raw_item in raw_items:
        try:
            item_result = process_raw_item(supabase, raw_item)
        except Exception as error:
            result["failed"] += 1
            print(f"raw_item={raw_item['id']} failed: {error}")
            continue

        if item_result["action"] == "saved":
            result["saved"] += item_result.get("saved_count", 1)
        elif item_result["action"] == "ignored":
            result["ignored"] += 1

        print(
            f"raw_item={item_result['raw_item_id']} "
            f"action={item_result['action']} "
            f"event_ids={','.join(item_result.get('event_ids') or []) or None} "
            f"event_statuses={','.join(item_result.get('event_statuses') or []) or None}"
        )

    return result


def check_duplicates() -> int:
    supabase = get_supabase_client()
    events = (
        supabase.table("events")
        .select("id,title,date_start,venue_name,status,source_url")
        .in_("status", ["published", "needs_review"])
        .order("date_start")
        .execute()
        .data
    )

    candidates = find_duplicate_candidates(events or [])
    print(f"duplicate_candidates={len(candidates)}")
    return len(candidates)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    if not args.skip_telegram:
        print("Step 1: Telegram ingestion")
        asyncio.run(ingest_telegram_posts())

    print("Step 2: OpenAI raw_items processing")
    processing_result = process_raw_items(args.process_limit)
    print(
        "processing_result="
        f"saved:{processing_result['saved']} "
        f"ignored:{processing_result['ignored']} "
        f"failed:{processing_result['failed']}"
    )

    if not args.skip_dedup_check:
        print("Step 3: Duplicate candidate check")
        check_duplicates()

    print("Pipeline finished.")


if __name__ == "__main__":
    main()
