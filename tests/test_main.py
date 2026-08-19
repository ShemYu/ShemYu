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
        fake_ai_module = types.ModuleType("src.ai")
        fake_ai_module.build_provider = Mock(return_value=provider)

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

        fake_ai_module.build_provider.assert_called_once_with(None, None)
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

    def test_cli_rejects_provider_and_model_without_jd(self):
        with self.assertRaises(SystemExit):
            parse_args(["--provider", "openai"])
        with self.assertRaises(SystemExit):
            parse_args(["--model", "gpt-5.6-luna"])

    def test_cli_accepts_provider_and_model_with_jd(self):
        args = parse_args(
            ["jd.txt", "--provider", "openai", "--model", "gpt-5.6-luna"]
        )
        self.assertEqual(args.target_jd, "jd.txt")
        self.assertEqual(args.provider, "openai")
        self.assertEqual(args.model, "gpt-5.6-luna")

    @patch("src.main.Jinja2Generator")
    @patch("src.main.YamlDataLoader")
    def test_jd_generation_forwards_provider_and_model(
        self, loader_class, generator_class
    ):
        profile = {"basics": {"name": "Test"}}
        tailored_profile = {"basics": {"name": "Tailored Test"}}
        loader_class.return_value.load.return_value = profile
        provider = Mock()
        provider.tailor_profile.return_value = tailored_profile
        fake_ai_module = types.ModuleType("src.ai")
        fake_ai_module.build_provider = Mock(return_value=provider)

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "data"))
            jd_path = os.path.join(project_dir, "jd.txt")
            with open(jd_path, "w", encoding="utf-8") as file:
                file.write("Senior AI Engineer")
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                with patch.dict(sys.modules, {"src.ai": fake_ai_module}):
                    main(jd_path, "cookpad_ai", "openai", "gpt-test")
            finally:
                os.chdir(previous_dir)

        fake_ai_module.build_provider.assert_called_once_with("openai", "gpt-test")
        provider.tailor_profile.assert_called_once_with(profile, "Senior AI Engineer")
        generator_class.return_value.generate_batch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
