from app.config import get_settings
from datetime import date
from supabase import create_client
import sys


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    settings = get_settings()

    if not settings.supabase_anon_key:
        raise RuntimeError("Missing SUPABASE_ANON_KEY in backend/.env")

    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
    response = (
        supabase.table("public_events")
        .select("title,date_start,date_end,venue_name,confidence_score,original_text", count="exact")
        .order("date_start")
        .execute()
    )

    print(f"public_events_count={response.count}")
    today = date.today().isoformat()
    visible_events = [
        event
        for event in response.data or []
        if (event.get("date_end") or event.get("date_start") or today) >= today
    ]
    print(f"frontend_visible_count={len(visible_events)}")
    with_original_text = [
        event for event in response.data or [] if event.get("original_text")
    ]
    print(f"with_original_text_count={len(with_original_text)}")

    for event in response.data or []:
        print(f"{event.get('date_start')} | {event.get('title')}")


if __name__ == "__main__":
    main()
