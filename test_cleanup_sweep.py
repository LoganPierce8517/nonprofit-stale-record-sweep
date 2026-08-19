import unittest

from cleanup_sweep import stale_records


class CleanupDecisionTest(unittest.TestCase):
    def test_only_records_past_retention_date_are_stale(self):
        records = [
            {"record_id": "r1", "retain_until": "2026-08-09"},
            {"record_id": "r2", "retain_until": "2026-08-10"},
            {"record_id": "r3", "retain_until": "2026-08-11"},
        ]
        self.assertEqual(["r1"], [item["record_id"] for item in stale_records(records, "2026-08-10")])


if __name__ == "__main__":
    unittest.main()
