#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fetch_job import derive_folder_slug, stage_job_description, search_jobs, scrape_job_posting, load_env_file
import os


class FetchJobTests(unittest.TestCase):
    def test_load_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("TEST_KEY_123=test_val_456\n# Comment\nINVALID_LINE\n", encoding="utf-8")
            os.environ.pop("TEST_KEY_123", None)
            load_env_file(env_file)
            self.assertEqual(os.environ.get("TEST_KEY_123"), "test_val_456")
    def test_derive_folder_slug(self) -> None:
        self.assertEqual(derive_folder_slug("Google", "SWE Intern"), "google-swe-intern")
        self.assertEqual(derive_folder_slug("Jane Street", "Quantitative Researcher (2025)"), "jane-street-quantitative-researcher-2025")
        self.assertEqual(derive_folder_slug("Meta", "Software Engineer - Mobile"), "meta-software-engineer-mobile")

    def test_stage_job_description(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test-app"
            content = "# Software Engineer\n\nRequirements:\n- Python\n- React"
            url = "https://example.com/jobs/123"

            out = stage_job_description(content, target, source_url=url)
            self.assertTrue(out.is_file())
            saved = out.read_text(encoding="utf-8")
            self.assertIn("<!-- Source: https://example.com/jobs/123 -->", saved)
            self.assertIn("# Software Engineer", saved)
            self.assertIn("- Python", saved)

    @patch("fetch_job.run_firecrawl_command")
    def test_search_jobs(self, mock_cmd: MagicMock) -> None:
        mock_output = {
            "success": True,
            "data": {
                "web": [
                    {"title": "Job 1", "url": "https://example.com/1", "description": "Desc 1"},
                    {"title": "Job 2", "url": "https://example.com/2", "description": "Desc 2"},
                ]
            }
        }
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["search"], returncode=0, stdout=json.dumps(mock_output)
        )

        results = search_jobs("software engineer intern", limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Job 1")
        self.assertEqual(results[1]["url"], "https://example.com/2")

    @patch("fetch_job.run_firecrawl_command")
    def test_scrape_job_posting(self, mock_cmd: MagicMock) -> None:
        mock_cmd.return_value = subprocess.CompletedProcess(
            args=["scrape"], returncode=0, stdout="# Engineer Role\nFull Details\n"
        )
        content = scrape_job_posting("https://example.com/job/1")
        self.assertIn("# Engineer Role", content)


if __name__ == "__main__":
    unittest.main()
