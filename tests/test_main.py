import os
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from src.main import CANONICAL_OUTPUTS, _tailored_outputs, main, parse_args


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

    def test_missing_jd_fails_before_loading_profile(self):
        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                with self.assertRaises(FileNotFoundError):
                    main("missing-jd.txt")
            finally:
                os.chdir(previous_dir)

    @patch("src.main.Jinja2Generator")
    @patch("src.main.YamlDataLoader")
    def test_jd_generation_uses_agent_and_safe_named_batch(
        self, loader_class, generator_class
    ):
        profile = {"basics": {"name": "Test"}}
        tailored_profile = {"basics": {"name": "Tailored Test"}}
        loader_class.return_value.load.return_value = profile
        provider = Mock()
        provider.tailor_profile.return_value = tailored_profile
        provider_class = Mock(return_value=provider)
        fake_ai_module = types.ModuleType("src.ai")
        fake_ai_module.OpenAIAgentProvider = provider_class

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            jd_path = os.path.join(project_dir, "jd.txt")
            with open(jd_path, "w", encoding="utf-8") as file:
                file.write("Senior AI Engineer")
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                with patch.dict(sys.modules, {"src.ai": fake_ai_module}):
                    main(jd_path, "cookpad_ai")
            finally:
                os.chdir(previous_dir)

        provider.tailor_profile.assert_called_once_with(profile, "Senior AI Engineer")
        generator_class.return_value.generate_batch.assert_called_once_with(
            tailored_profile,
            (
                ("resume.md.j2", "output/tailored/cookpad_ai.md"),
                ("resume.html.j2", "output/tailored/cookpad_ai.html"),
                ("resume_bible.html.j2", "output/tailored/cookpad_ai_bible.html"),
            ),
        )

    def test_rejects_output_path_traversal(self):
        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            jd_path = os.path.join(project_dir, "jd.txt")
            with open(jd_path, "w", encoding="utf-8") as file:
                file.write("Senior AI Engineer")
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                with self.assertRaisesRegex(ValueError, "Output name"):
                    main(jd_path, "../escape")
            finally:
                os.chdir(previous_dir)

    def test_tailored_resume_basename_cannot_collide_with_canonical_outputs(self):
        canonical_paths = {path for _, path in CANONICAL_OUTPUTS}
        tailored_paths = {path for _, path in _tailored_outputs("resume")}

        self.assertTrue(canonical_paths.isdisjoint(tailored_paths))
        self.assertTrue(
            all(path.startswith("output/tailored/") for path in tailored_paths)
        )

    def test_cli_rejects_custom_output_without_jd(self):
        with self.assertRaises(SystemExit):
            parse_args(["--output-name", "custom"])

    def test_cli_allows_locale_select_and_pdf(self):
        args = parse_args(["--locale", "ja", "--select", "ly_agent", "--pdf"])
        self.assertEqual(args.locale, "ja")
        self.assertEqual(args.select, "ly_agent")
        self.assertTrue(args.pdf)

    @patch("src.i18n.translate_profile")
    @patch("src.select.apply_selection")
    @patch("src.select.load_selection")
    @patch("src.main.Jinja2Generator")
    @patch("src.main.YamlDataLoader")
    def test_locale_select_renders_ja_html_without_ai(
        self, loader_class, generator_class, load_selection, apply_selection, translate_profile
    ):
        profile = {"basics": {"name": "Shem Yu"}}
        loader_class.return_value.load.return_value = profile
        load_selection.return_value = {
            "meta": {"output_name": "ShemYu_Resume_LY_Agent_JP", "application_id": "ly00493"}
        }
        apply_selection.return_value = {"basics": {"name": "Selected"}}
        translate_profile.return_value = ({"basics": {"name": "余顯漁（Shem Yu）"}}, [])

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main(locale="ja", select="ly_agent")
            finally:
                os.chdir(previous_dir)

        load_selection.assert_called_once_with("ly_agent")
        generator_class.return_value.generate_batch.assert_called_once()
        rendered_profile, outputs = generator_class.return_value.generate_batch.call_args[0]
        self.assertEqual(
            outputs,
            (("resume_ja.html.j2", "output/ShemYu_Resume_LY_Agent_JP.html"),),
        )
        self.assertEqual(rendered_profile["basics"]["name"], "余顯漁（Shem Yu）")
        self.assertIn("generated_on", rendered_profile)
        self.assertEqual(rendered_profile["selection_meta"]["application_id"], "ly00493")


if __name__ == "__main__":
    unittest.main()
