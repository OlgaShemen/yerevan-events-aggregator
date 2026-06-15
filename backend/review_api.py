from datetime import UTC, date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
from urllib.parse import parse_qs, urlparse

from app.db import get_supabase_client


HOST = os.getenv("REVIEW_API_HOST", "127.0.0.1")
PORT = int(os.getenv("REVIEW_API_PORT", "8000"))

ALLOWED_UPDATE_FIELDS = {
    "title",
    "description",
    "category",
    "language",
    "date_start",
    "time_start",
    "date_end",
    "time_end",
    "venue_name",
    "address",
    "price_text",
    "source_url",
    "category_checked",
}

EVENT_SELECT_FIELDS = (
    "id,title,description,original_text,category,language,date_start,time_start,"
    "date_end,time_end,venue_name,address,price_text,status,confidence_score,source_url,"
    "category_checked,created_at,updated_at,ai_payload"
)


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def normalize_empty_values(payload: dict) -> dict:
    normalized = {}

    for key, value in payload.items():
        if key not in ALLOWED_UPDATE_FIELDS:
            continue

        if isinstance(value, str):
            value = value.strip()
            normalized[key] = value if value else None
        else:
            normalized[key] = value

    return normalized


def get_event(supabase, event_id: str) -> dict:
    event = (
        supabase.table("events")
        .select("id,title,status")
        .eq("id", event_id)
        .limit(1)
        .execute()
        .data
    )

    if not event:
        raise ValueError(f"Event not found: {event_id}")

    return event[0]


def write_log(supabase, event_id: str, status: str, message: str, details: dict) -> None:
    supabase.table("processing_logs").insert(
        {
            "event_id": event_id,
            "step": "review_api",
            "status": status,
            "message": message,
            "details": details,
        }
    ).execute()


class ReviewApiHandler(BaseHTTPRequestHandler):
    supabase = None

    def do_OPTIONS(self) -> None:
        self.send_empty(204)

    def do_GET(self) -> None:
        try:
            path = urlparse(self.path).path

            if path == "/health":
                self.send_json({"ok": True})
                return

            if path == "/review/events":
                self.handle_list_events()
                return

            self.send_json({"error": "Not found"}, status=404)
        except Exception as error:
            self.send_error_json(error)

    def do_PATCH(self) -> None:
        try:
            event_id = self.match_event_action(action=None)
            if not event_id:
                self.send_json({"error": "Not found"}, status=404)
                return

            self.handle_update_event(event_id)
        except Exception as error:
            self.send_error_json(error)

    def do_POST(self) -> None:
        try:
            event_id = self.match_event_action(action="publish")
            if event_id:
                self.handle_publish_event(event_id)
                return

            event_id = self.match_event_action(action="reject")
            if event_id:
                self.handle_reject_event(event_id)
                return

            self.send_json({"error": "Not found"}, status=404)
        except Exception as error:
            self.send_error_json(error)

    def handle_list_events(self) -> None:
        query = parse_qs(urlparse(self.path).query)
        status = (query.get("status") or ["needs_review"])[0]
        search = ((query.get("search") or [""])[0] or "").strip().lower()
        category_unchecked_only = (query.get("category_unchecked") or [""])[0] == "1"

        if status not in {"needs_review", "published"}:
            self.send_json({"error": "Unsupported status."}, status=400)
            return

        today = date.today().isoformat()
        request = (
            self.supabase.table("events")
            .select(EVENT_SELECT_FIELDS)
            .eq("status", status)
        )

        if status == "needs_review":
            request = request.or_(f"date_start.is.null,date_start.gte.{today}")

        if status == "published":
            request = (
                request
                .or_(f"date_end.gte.{today},and(date_end.is.null,date_start.gte.{today})")
                .order("date_start")
                .order("time_start")
                .limit(300)
            )
            if category_unchecked_only:
                request = request.eq("category_checked", False)
        else:
            request = request.order("created_at")

        events = request.execute().data or []

        if search:
            events = [
                event
                for event in events
                if search
                in " ".join(
                    str(event.get(field) or "")
                    for field in [
                        "title",
                        "description",
                        "venue_name",
                        "address",
                        "price_text",
                        "category",
                        "language",
                    ]
                ).lower()
            ]

        self.send_json({"events": events})

    def handle_update_event(self, event_id: str) -> None:
        event = get_event(self.supabase, event_id)
        payload = self.read_json()
        updates = normalize_empty_values(payload)

        if not updates:
            self.send_json(
                {"error": "No allowed fields to update."},
                status=400,
            )
            return

        updates["updated_at"] = now_iso()
        updated = (
            self.supabase.table("events")
            .update(updates)
            .eq("id", event_id)
            .execute()
            .data
        )
        write_log(
            self.supabase,
            event_id,
            "success",
            "Event was updated from review API.",
            {"previous_status": event["status"], "updates": updates},
        )
        self.send_json({"event": updated[0] if updated else None})

    def handle_publish_event(self, event_id: str) -> None:
        event = get_event(self.supabase, event_id)
        updated = (
            self.supabase.table("events")
            .update({"status": "published", "updated_at": now_iso()})
            .eq("id", event_id)
            .execute()
            .data
        )
        write_log(
            self.supabase,
            event_id,
            "success",
            "Event was published from review API.",
            {"previous_status": event["status"]},
        )
        self.send_json({"event": updated[0] if updated else None})

    def handle_reject_event(self, event_id: str) -> None:
        event = get_event(self.supabase, event_id)
        payload = self.read_json(required=False)
        reason = payload.get("reason") or "Rejected from review API."
        updated = (
            self.supabase.table("events")
            .update({"status": "rejected", "updated_at": now_iso()})
            .eq("id", event_id)
            .execute()
            .data
        )
        write_log(
            self.supabase,
            event_id,
            "success",
            "Event was rejected from review API.",
            {"previous_status": event["status"], "reason": reason},
        )
        self.send_json({"event": updated[0] if updated else None})

    def match_event_action(self, action: str | None) -> str | None:
        parts = [part for part in urlparse(self.path).path.split("/") if part]

        if action is None and len(parts) == 3 and parts[:2] == ["review", "events"]:
            return parts[2]

        if len(parts) == 4 and parts[:2] == ["review", "events"] and parts[3] == action:
            return parts[2]

        return None

    def read_json(self, required: bool = True) -> dict:
        raw_length = self.headers.get("Content-Length", "0")
        length = int(raw_length)

        if length == 0:
            if required:
                raise ValueError("Missing JSON body.")
            return {}

        raw_body = self.rfile.read(length).decode("utf-8")
        return json.loads(raw_body)

    def send_empty(self, status: int) -> None:
        self.send_response(status)
        self.add_common_headers()
        self.end_headers()

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.add_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, error: Exception) -> None:
        status = 400 if isinstance(error, ValueError) else 500
        self.send_json({"error": str(error)}, status=status)

    def add_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Methods", "GET, PATCH, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ReviewApiHandler.supabase = get_supabase_client()
    server = ThreadingHTTPServer((HOST, PORT), ReviewApiHandler)
    print(f"Review API running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
