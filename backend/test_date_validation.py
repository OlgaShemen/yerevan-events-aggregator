import unittest

from app.date_validation import (
    clear_inferred_weekday_dates,
    has_weekday_without_concrete_date,
    telegram_publication_date,
)


class DateValidationTests(unittest.TestCase):
    def test_keeps_english_month_before_day(self):
        text = "Saturday, July 11 at 18:00"
        self.assertFalse(has_weekday_without_concrete_date(text))

    def test_keeps_day_before_english_month(self):
        text = "Saturday, 11 July at 18:00"
        self.assertFalse(has_weekday_without_concrete_date(text))

    def test_keeps_full_english_month_name(self):
        text = "Tuesday, September 8 at 21:00"
        self.assertFalse(has_weekday_without_concrete_date(text))

    def test_clears_date_for_weekday_only_schedule(self):
        event = {"date_start": "2026-09-06", "date_end": None}
        result = clear_inferred_weekday_dates(event, "По воскресеньям в 18:00")
        self.assertIsNone(result["date_start"])

    def test_allows_explicit_tomorrow_reference(self):
        text = "Завтра (в воскресенье) в 19:00 встреча киноклуба"
        self.assertFalse(has_weekday_without_concrete_date(text))

    def test_converts_telegram_timestamp_to_yerevan_date(self):
        self.assertEqual(
            telegram_publication_date("2026-09-05T21:30:00+00:00"),
            "2026-09-06",
        )

    def test_rejects_timestamp_without_timezone(self):
        self.assertIsNone(telegram_publication_date("2026-09-05T21:30:00"))


if __name__ == "__main__":
    unittest.main()
