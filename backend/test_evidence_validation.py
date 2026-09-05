import unittest

from app.evidence_validation import quote_exists_in_source, validate_event_evidence


class EvidenceValidationTests(unittest.TestCase):
    def test_accepts_exact_quotes_with_whitespace_normalization(self):
        raw = "Встречаемся  8 сентября\nв 19:00 в LAN."
        self.assertTrue(quote_exists_in_source("8 сентября", raw))
        self.assertTrue(quote_exists_in_source("в 19:00 в LAN", raw))

    def test_rejects_quote_not_present_in_source(self):
        self.assertFalse(quote_exists_in_source("9 сентября", "Встречаемся 8 сентября"))

    def test_confirms_supported_event_fields(self):
        event = {
            "date_start": "2026-09-08",
            "time_start": "19:00",
            "venue_name": "LAN",
            "date_evidence": ["8 сентября"],
            "time_evidence": ["19:00"],
            "venue_evidence": ["LAN"],
        }
        result = validate_event_evidence(event, "8 сентября в 19:00 встречаемся в LAN")
        self.assertTrue(result["evidence_validation"]["date"]["confirmed"])
        self.assertTrue(result["evidence_validation"]["time"]["confirmed"])
        self.assertTrue(result["evidence_validation"]["place"]["confirmed"])

    def test_marks_invented_date_as_unconfirmed(self):
        event = {
            "date_start": "2026-09-09",
            "date_evidence": ["9 сентября"],
            "time_evidence": [],
            "venue_evidence": [],
        }
        result = validate_event_evidence(event, "Встречаемся 8 сентября")
        self.assertFalse(result["evidence_validation"]["date"]["confirmed"])

    def test_trusted_directory_confirms_resolved_place(self):
        event = {
            "venue_name": "Ari Standup Club",
            "address": "ул. Вардананц, 18/1",
            "venue_resolution": "trusted_directory",
            "date_evidence": [],
            "time_evidence": [],
            "venue_evidence": ["https://aristandupclub.am/"],
        }
        result = validate_event_evidence(event, "Билеты https://aristandupclub.am/")
        self.assertTrue(result["evidence_validation"]["place"]["confirmed"])
        self.assertEqual(
            result["evidence_validation"]["place"]["method"],
            "trusted_directory",
        )


if __name__ == "__main__":
    unittest.main()
