#!/usr/bin/env python3
import datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from applied_jobs import (
    convert_sheet_url_to_csv_url,
    normalize_company,
    normalize_role,
    parse_csv_records,
    fetch_sheet_records,
    check_applied,
)


class AppliedJobsTests(unittest.TestCase):
    def test_convert_sheet_url_to_csv_url(self) -> None:
        raw_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        expected = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv&gid=0"
        self.assertEqual(convert_sheet_url_to_csv_url(raw_url), expected)

        gid_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=123456"
        expected_gid = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/export?format=csv&gid=123456"
        self.assertEqual(convert_sheet_url_to_csv_url(gid_url), expected_gid)

    def test_normalize_company(self) -> None:
        self.assertEqual(normalize_company("Google Inc."), "google")
        self.assertEqual(normalize_company("Meta Platforms, LLC"), "meta")
        self.assertEqual(normalize_company("Palantir Technologies"), "palantir")

    def test_normalize_role(self) -> None:
        self.assertEqual(normalize_role("Software Engineering Intern (Summer 2027)"), "software engineer intern")
        self.assertEqual(normalize_role("SWE Intern - Summer 2025"), "software engineer intern")
        self.assertEqual(normalize_role("Machine Learning Engineer Intern"), "machine learning engineer intern")

    def test_parse_csv_records(self) -> None:
        csv_text = "Company,Role,Date Applied\nGoogle,Software Engineer Intern,2026-10-01\nMeta,Data Science Intern,2026-10-05\n"
        records = parse_csv_records(csv_text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["company"], "Google")
        self.assertEqual(records[0]["role"], "Software Engineer Intern")
        self.assertEqual(records[1]["company"], "Meta")

    def test_check_applied_matches(self) -> None:
        applied_records = [
            {"company": "Google", "role": "Software Engineering Intern", "raw": {}},
            {"company": "Meta", "role": "Data Scientist Intern (Summer 2027)", "raw": {}},
            {"company": "Jane Street", "role": "Quantitative Researcher", "raw": {}},
        ]

        # Exact / fuzzy match Google SWE
        match1 = check_applied("Google Inc", "SWE Intern Summer 2027", applied_records)
        self.assertIsNotNone(match1)
        self.assertEqual(match1["company"], "Google")

        # Fuzzy match Meta Data Scientist
        match2 = check_applied("Meta Platforms", "Data Science Intern", applied_records)
        self.assertIsNotNone(match2)
        self.assertEqual(match2["company"], "Meta")

        # Not applied role at Google
        match3 = check_applied("Google", "Legal Counsel", applied_records)
        self.assertIsNone(match3)

        # Company not applied
        match4 = check_applied("Apple", "Software Engineer", applied_records)
        self.assertIsNone(match4)

    @patch("urllib.request.urlopen")
    def test_daily_saving_and_reuse(self, mock_urlopen: MagicMock) -> None:
        today = datetime.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "applied_jobs.json"

            # 1. First fetch saves locally with today's date
            mock_resp = MagicMock()
            mock_resp.read.return_value = b"Company,Role\nDatabricks,Software Engineer\n"
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            recs = fetch_sheet_records("https://example.com/sheet", saved_path=save_path)
            self.assertEqual(len(recs), 1)
            self.assertEqual(recs[0]["company"], "Databricks")
            self.assertTrue(save_path.is_file())

            saved_content = json.loads(save_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_content.get("last_synced"), today)
            self.assertEqual(saved_content.get("count"), 1)

            # 2. Subsequent call today reuses saved snapshot without calling urlopen
            mock_urlopen.reset_mock()
            recs2 = fetch_sheet_records("https://example.com/sheet", saved_path=save_path)
            self.assertEqual(len(recs2), 1)
            mock_urlopen.assert_not_called()

            # 3. Force refresh triggers new fetch
            fetch_sheet_records("https://example.com/sheet", saved_path=save_path, force_refresh=True)
            mock_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()
