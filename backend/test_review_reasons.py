import unittest
from datetime import date

from app.review_reasons import build_review_reasons


TODAY = date(2026, 9, 5)


class ReviewReasonTests(unittest.TestCase):
    def test_complete_event_has_no_review_reasons(self):
        event = {
            "date_start": "2026-09-10",
            "venue_name": "LAN",
            "confidence_score": 0.9,
        }
        self.assertEqual(build_review_reasons(event, today=TODAY), [])

    def test_reports_all_relevant_reasons(self):
        event = {
            "date_start": None,
            "date_end": None,
            "venue_name": None,
            "address": None,
            "confidence_score": 0.7,
            "ai_payload": {"duplicate_candidate": {"event_id": "existing"}},
        }
        self.assertEqual(
            build_review_reasons(event, today=TODAY),
            ["missing_date", "missing_place", "low_confidence", "possible_duplicate"],
        )

    def test_active_recurring_schedule_counts_as_date(self):
        event = {
            "date_start": None,
            "date_end": None,
            "recurring_schedule": "Ежедневно",
            "display_until": "2026-09-06",
            "address": "ЖД вокзал",
            "confidence_score": 0.9,
        }
        self.assertEqual(build_review_reasons(event, today=TODAY), [])

    def test_expired_recurring_schedule_needs_date(self):
        event = {
            "recurring_schedule": "Ежедневно",
            "display_until": "2026-09-04",
            "address": "ЖД вокзал",
            "confidence_score": 0.9,
        }
        self.assertEqual(build_review_reasons(event, today=TODAY), ["missing_date"])


if __name__ == "__main__":
    unittest.main()
