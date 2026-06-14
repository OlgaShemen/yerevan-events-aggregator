import argparse

from app.db import get_supabase_client
from process_raw_item_to_event import process_raw_item


def get_raw_items(supabase, limit: int) -> list[dict]:
    response = (
        supabase.table("raw_items")
        .select("id,source_id,source_url,raw_text,status")
        .eq("status", "new")
        .order("collected_at")
        .limit(limit)
        .execute()
    )

    return response.data or []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process raw_items with OpenAI and save real events."
    )
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    supabase = get_supabase_client()
    raw_items = get_raw_items(supabase, args.limit)

    if not raw_items:
        print("No raw items with status=new found.")
        return

    saved = 0
    ignored = 0
    failed = 0

    for raw_item in raw_items:
        try:
            result = process_raw_item(supabase, raw_item)
        except Exception as error:
            failed += 1
            print(f"raw_item={raw_item['id']} failed: {error}")
            continue

        if result["action"] == "saved":
            saved += result.get("saved_count", 1)
        elif result["action"] == "ignored":
            ignored += 1

        print(
            f"raw_item={result['raw_item_id']} "
            f"action={result['action']} "
            f"event_ids={','.join(result.get('event_ids') or []) or None} "
            f"event_statuses={','.join(result.get('event_statuses') or []) or None}"
        )

    print("Batch processing finished.")
    print(f"saved={saved}")
    print(f"ignored={ignored}")
    print(f"failed={failed}")


if __name__ == "__main__":
    main()
