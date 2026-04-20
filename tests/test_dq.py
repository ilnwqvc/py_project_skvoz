import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dq import check_non_empty, check_not_null, check_numeric_range, check_unique_key


class TestDQChecks(unittest.TestCase):
    def test_check_non_empty_positive(self):
        df = pd.DataFrame({"city_id": ["JP_TYO"]})
        rule = {"name": "non_empty_test", "type": "non_empty", "severity": "FAIL"}

        result = check_non_empty(df, rule)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["details"]["row_count"], 1)

    def test_check_unique_key_negative(self):
        df = pd.DataFrame(
            {
                "city_id": ["JP_TYO", "JP_TYO"],
                "ts": ["2026-02-01 00:00:00", "2026-02-01 00:00:00"],
            }
        )
        rule = {
            "name": "unique_key_test",
            "type": "unique_key",
            "severity": "FAIL",
            "columns": ["city_id", "ts"],
        }

        result = check_unique_key(df, rule)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["details"]["duplicate_rows"], 2)

    def test_check_numeric_range_boundary(self):
        df = pd.DataFrame({"precipitation": [0, 10, 25]})
        rule = {
            "name": "precipitation_range_test",
            "type": "numeric_range",
            "severity": "FAIL",
            "column": "precipitation",
            "min": 0,
            "max": 25,
        }

        result = check_numeric_range(df, rule)

        self.assertEqual(result["status"], "PASS")

    def test_check_not_null_negative(self):
        df = pd.DataFrame({"ts": ["2026-02-01 00:00:00", None], "city_id": ["JP_TYO", "JP_TYO"]})
        rule = {
            "name": "not_null_test",
            "type": "not_null",
            "severity": "FAIL",
            "columns": ["ts", "city_id"],
        }

        result = check_not_null(df, rule)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["details"]["null_counts"]["ts"], 1)


if __name__ == "__main__":
    unittest.main()
