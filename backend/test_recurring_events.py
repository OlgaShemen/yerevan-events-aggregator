import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from app.recurring_events import prepare_recurring_event, recurring_event_expired
from process_raw_item_to_event import choose_event_status, process_raw_item, save_event
from review_api import ReviewApiHandler


SCHEDULE = "ЕЖЕДНЕВНО:\n1 ГРУППА: 09:00 - 15:00\n2 ГРУППА: 16:00 - 22:00"


class RecurringEventTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch("app.recurring_events.yerevan_today", return_value=date(2026, 9, 4))
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.review_clock = patch("app.review_reasons.yerevan_today", return_value=date(2026, 9, 4))
        self.review_clock.start()
        self.addCleanup(self.review_clock.stop)
        self.event = {
            "title": "SUP-тур", "recurring_schedule": SCHEDULE,
            "date_start": None, "date_end": None,
            "venue_name": "ЖД вокзал", "confidence_score": 0.9,
        }
        self.raw = {
            "id": "post-1", "source_id": "channel-1",
            "raw_text": "SUP-тур. " + SCHEDULE,
            "raw_payload": {"telegram_date": "2026-09-03T10:00:00+00:00"},
        }

    def test_daily_groups_remain_one_undated_offer_until_sunday(self):
        event = prepare_recurring_event(self.event, self.raw)
        self.assertEqual(event["display_until"], "2026-09-06")
        self.assertEqual(event["recurring_schedule"], SCHEDULE)
        self.assertIsNone(event["date_start"])
        self.assertIsNone(event["date_end"])
        self.assertEqual(choose_event_status(event), "published")

    def test_expires_on_monday_not_sunday(self):
        event = prepare_recurring_event(self.event, self.raw)
        self.assertFalse(recurring_event_expired(event, date(2026, 9, 6)))
        self.assertTrue(recurring_event_expired(event, date(2026, 9, 7)))

    def test_old_post_never_renews_from_collection_or_processing_date(self):
        self.raw["raw_payload"]["telegram_date"] = "2026-08-25T10:00:00+00:00"
        self.raw["collected_at"] = "2026-09-04T10:00:00+00:00"
        event = prepare_recurring_event(self.event, self.raw)
        self.assertEqual(event["display_until"], "2026-08-30")
        self.assertTrue(recurring_event_expired(event))

    def test_publication_week_uses_yerevan_midnight(self):
        self.raw["raw_payload"]["telegram_date"] = "2026-08-30T20:01:00+00:00"
        self.assertEqual(prepare_recurring_event(self.event, self.raw)["display_until"], "2026-09-06")
        self.raw["raw_payload"]["telegram_date"] = "2026-08-30T19:59:00+00:00"
        self.assertEqual(prepare_recurring_event(self.event, self.raw)["display_until"], "2026-08-30")

    def test_new_post_next_week_gets_a_new_window(self):
        first = prepare_recurring_event(self.event, self.raw)
        self.raw["raw_payload"]["telegram_date"] = "2026-09-07T10:00:00+00:00"
        with patch("app.recurring_events.yerevan_today", return_value=date(2026, 9, 7)):
            second = prepare_recurring_event(self.event, self.raw)
        self.assertEqual(first["display_until"], "2026-09-06")
        self.assertEqual(second["display_until"], "2026-09-13")

    def test_missing_invalid_and_naive_source_dates_stay_in_review(self):
        for value in [None, "invalid", "2026-09-04T10:00:00"]:
            with self.subTest(value=value):
                self.raw["raw_payload"]["telegram_date"] = value
                event = prepare_recurring_event(self.event, self.raw)
                self.assertIsNone(event["display_until"])
                self.assertEqual(choose_event_status(event), "needs_review")

    def test_plain_weekday_or_this_week_is_not_recurring(self):
        for schedule in ["Четверг: 18:00", "На этой неделе", "Лето", ""]:
            with self.subTest(schedule=schedule):
                self.raw["raw_text"] = schedule
                event = prepare_recurring_event({**self.event, "recurring_schedule": schedule}, self.raw)
                self.assertIsNone(event["display_until"])

    def test_recurring_schedule_must_be_quoted_from_source(self):
        self.raw["raw_text"] = "SUP-тур по предварительной записи"
        self.assertIsNone(prepare_recurring_event(self.event, self.raw)["display_until"])

    def test_explicitly_dated_event_is_preserved(self):
        self.event["date_start"] = "2026-09-05"
        event = prepare_recurring_event(self.event, self.raw)
        self.assertEqual(event["date_start"], "2026-09-05")
        self.assertIsNone(event["display_until"])

    def test_same_week_reimport_preserves_existing_card_and_moderation(self):
        event = prepare_recurring_event(self.event, self.raw)
        client = MagicMock()
        existing = {"id": "already-saved", "status": "archived"}
        client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [existing]
        result = save_event(client, self.raw, event)
        self.assertEqual(result, existing)
        client.table.return_value.insert.assert_not_called()
        key = client.table.return_value.select.return_value.eq.call_args.args[1]
        self.assertTrue(key.startswith("weekly:2026-09-06:channel-1:"))

    def test_expired_offer_is_ignored_without_database_event_insert(self):
        self.raw["raw_payload"]["telegram_date"] = "2026-08-25T10:00:00+00:00"
        client = MagicMock()
        with patch("process_raw_item_to_event.extract_event_from_text", return_value={
            "is_event": True, "events": [self.event],
        }), patch("process_raw_item_to_event.save_event") as save:
            result = process_raw_item(client, self.raw)
        self.assertEqual(result["action"], "ignored")
        save.assert_not_called()

    def test_admin_cannot_publish_expired_offer(self):
        handler = object.__new__(ReviewApiHandler)
        handler.supabase = MagicMock()
        with patch("review_api.get_event", return_value={"display_until": "2026-08-30"}):
            with self.assertRaises(ValueError):
                handler.handle_publish_event("expired")
        handler.supabase.table.assert_not_called()


if __name__ == "__main__":
    unittest.main()
