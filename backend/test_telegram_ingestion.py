import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.telegram_ingestion import (
    extract_explicit_source_url,
    forwarded_public_url,
    message_to_raw_payload,
    private_message_source_url,
    save_raw_message,
)


class TelegramIngestionTests(unittest.TestCase):
    def test_private_message_saved_once_as_normal_new_raw_item(self):
        supabase = MagicMock()
        query = supabase.table.return_value
        query.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = [
            SimpleNamespace(data=[]), SimpleNamespace(data=[{"id": "existing"}])]
        message = SimpleNamespace(id=7, message="Event announcement",
                                  date=datetime(2026, 9, 9, 12, tzinfo=UTC))
        args = (supabase, {"id": "source"}, "Manual", message, None, 4305873550)
        self.assertTrue(save_raw_message(*args))
        self.assertFalse(save_raw_message(*args))
        query.insert.assert_called_once()
        saved = query.insert.call_args.args[0]
        self.assertEqual(saved["status"], "new")
        self.assertIsNone(saved["source_url"])
        self.assertEqual(saved["raw_text"], message.message)

    def test_rejects_private_telegram_links(self):
        for url in ("https://t.me/c/123/4", "https://t.me/+invite", "https://t.me/joinchat/secret"):
            self.assertIsNone(extract_explicit_source_url("Источник: " + url))

    def test_forward_without_public_username_has_no_link(self):
        message = SimpleNamespace(message="Event", forward=SimpleNamespace(
            chat=SimpleNamespace(username=None), channel_post=123))
        self.assertIsNone(private_message_source_url(message))

    def test_forward_uses_original_date_only_for_private_source(self):
        original_date = datetime(2026, 9, 1, 12, tzinfo=UTC)
        message = SimpleNamespace(id=7, date=datetime(2026, 9, 9, 12, tzinfo=UTC),
                                  fwd_from=SimpleNamespace(date=original_date))
        private = message_to_raw_payload("Manual", message, None, 4305873550)
        public = message_to_raw_payload("public", message, "https://t.me/public/7")
        self.assertEqual(private["telegram_date"], original_date.isoformat())
        self.assertEqual(public["telegram_date"], message.date.isoformat())

    def test_extracts_explicit_source_url(self):
        text = "Название события\nИсточник: https://example.com/events/42."

        self.assertEqual(
            extract_explicit_source_url(text),
            "https://example.com/events/42",
        )

    def test_extracts_forwarded_public_telegram_url(self):
        message = SimpleNamespace(
            forward=SimpleNamespace(
                chat=SimpleNamespace(username="public_channel"),
                channel_post=123,
            )
        )

        self.assertEqual(
            forwarded_public_url(message),
            "https://t.me/public_channel/123",
        )

    def test_explicit_source_has_priority_for_private_message(self):
        message = SimpleNamespace(
            message="Источник: https://tickets.example/event",
            forward=SimpleNamespace(
                chat=SimpleNamespace(username="public_channel"),
                channel_post=123,
            ),
        )

        self.assertEqual(
            private_message_source_url(message),
            "https://tickets.example/event",
        )

    def test_private_payload_does_not_invent_public_url(self):
        message = SimpleNamespace(
            id=7,
            date=datetime(2026, 9, 9, 12, 0, tzinfo=UTC),
        )

        payload = message_to_raw_payload(
            "YerevanEventsManual",
            message,
            source_url=None,
            private_channel_id=4305873550,
        )

        self.assertIsNone(payload["telegram_url"])
        self.assertTrue(payload["manual_submission"])
        self.assertEqual(payload["telegram_channel_id"], 4305873550)


if __name__ == "__main__":
    unittest.main()
