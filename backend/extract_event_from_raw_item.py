import json

from app.db import get_supabase_client
from app.event_extraction import extract_event_from_text


def get_next_raw_item(supabase) -> dict | None:
    response = (
        supabase.table("raw_items")
        .select("id,source_id,source_url,raw_text,status")
        .eq("status", "new")
        .order("collected_at")
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def write_log(supabase, raw_item: dict, status: str, message: str, details: dict) -> None:
    supabase.table("processing_logs").insert(
        {
            "source_id": raw_item["source_id"],
            "raw_item_id": raw_item["id"],
            "step": "ai_event_extraction",
            "status": status,
            "message": message,
            "details": details,
        }
    ).execute()


def main() -> None:
    supabase = get_supabase_client()
    raw_item = get_next_raw_item(supabase)

    if not raw_item:
        print("No raw items with status=new found.")
        return

    try:
        extracted_event = extract_event_from_text(
            raw_text=raw_item["raw_text"],
            source_url=raw_item.get("source_url"),
        )
    except Exception as error:
        write_log(
            supabase=supabase,
            raw_item=raw_item,
            status="failed",
            message="AI extraction failed.",
            details={"error": str(error)},
        )
        raise

    write_log(
        supabase=supabase,
        raw_item=raw_item,
        status="success",
        message="AI extraction completed.",
        details={"extracted_event": extracted_event},
    )

    print("AI extraction works.")
    print(json.dumps(extracted_event, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
