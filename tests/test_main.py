import os
import tempfile
import unittest
from unittest.mock import patch

from src.main import CANONICAL_OUTPUTS, main, parse_args


class MainTest(unittest.TestCase):
    @patch("src.main.Jinja2Generator")
    @patch("src.main.YamlDataLoader")
    def test_default_generation_uses_one_canonical_batch(
        self, loader_class, generator_class
    ):
        profile = {"basics": {"name": "Test"}}
        loader_class.return_value.load.return_value = profile

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main()
            finally:
                os.chdir(previous_dir)

        generator_class.return_value.generate_batch.assert_called_once_with(
            profile, CANONICAL_OUTPUTS
        )

    def test_cli_language_defaults_to_en_and_accepts_ja(self):
        args = parse_args([])
        self.assertEqual(args.language, "en")
        args = parse_args(["--language", "ja"])
        self.assertEqual(args.language, "ja")

    def test_cli_rejects_job_description_positional(self):
        with self.assertRaises(SystemExit):
            parse_args(["target_jd.txt"])

    def test_cli_rejects_removed_output_name_flag(self):
        with self.assertRaises(SystemExit):
            parse_args(["--output-name", "custom"])

    @patch("src.pdf.render_and_assert_one_page", return_value=1)
    @patch("src.main.Jinja2Generator")
    @patch("src.main.YamlDataLoader")
    def test_language_ja_localizes_and_runs_one_page_check(
        self, loader_class, generator_class, pdf_check
    ):
        profile = {
            "basics": {
                "name": "Shem Yu",
                "label": "Senior AI Engineer @ Cookpad | GenAI, AI Agents & MLOps | Tokyo",
                "summary": "Applied AI engineer with 6 years building production agents.",
                "location": {"city": "Taipei", "region": "Taiwan"},
            },
            "work": [
                {
                    "name": "Cookpad",
                    "position": "Senior AI Engineer",
                    "startDate": "2026-02",
                    "endDate": "Present",
                    "highlights": [
                        "Built a multimodal coaching agent that reasons over cooking video and learner voice to decide whether to reteach, narrow, or advance; raised expert-grounded coverage from 40% to 95%."
                    ],
                }
            ],
            "education": [],
            "skills": [],
            "certificates": [],
            "publications": [],
            "projects": [],
        }
        loader_class.return_value.load.return_value = profile

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main("ja")
            finally:
                os.chdir(previous_dir)

        generator_class.assert_called_once_with("templates", language="ja")
        generate_batch = generator_class.return_value.generate_batch
        generate_batch.assert_called_once()
        localized = generate_batch.call_args.args[0]
        self.assertEqual(localized["basics"]["name"], "余顯漁（Shem Yu）")
        self.assertEqual(generate_batch.call_args.args[1], CANONICAL_OUTPUTS)
        pdf_check.assert_called_once_with(
            "output/resume.html",
            "output/resume.pdf",
        )


if __name__ == "__main__":
    unittest.main()
