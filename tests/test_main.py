import os
import tempfile
import unittest
from unittest.mock import call, patch

from src.main import main


class MainTest(unittest.TestCase):
    @patch('src.main.GeminiAIProvider')
    @patch('src.main.Jinja2Generator')
    @patch('src.main.YamlDataLoader')
    def test_default_generation_writes_canonical_outputs_without_ai(
        self, loader_class, generator_class, ai_class
    ):
        loader_class.return_value.load.return_value = {'basics': {'name': 'Test'}}

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, 'data'))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main()
            finally:
                os.chdir(previous_dir)

        ai_class.assert_not_called()
        self.assertEqual(
            generator_class.return_value.generate.call_args_list,
            [
                call({'basics': {'name': 'Test'}}, 'resume.md.j2', 'RESUME.md'),
                call({'basics': {'name': 'Test'}}, 'resume.html.j2', 'output/resume.html'),
                call({'basics': {'name': 'Test'}}, 'resume_bible.html.j2', 'output/resume_bible.html'),
                call({'basics': {'name': 'Test'}}, 'readme.md.j2', 'README.md'),
            ],
        )

    def test_missing_jd_fails_instead_of_generating_full_resume(self):
        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, 'data'))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                with self.assertRaises(FileNotFoundError):
                    main('missing-jd.txt')
            finally:
                os.chdir(previous_dir)

    @patch('src.main.GeminiAIProvider')
    @patch('src.main.Jinja2Generator')
    @patch('src.main.YamlDataLoader')
    def test_jd_generation_writes_only_tailored_outputs(
        self, loader_class, generator_class, ai_class
    ):
        profile = {'basics': {'name': 'Test'}}
        tailored_profile = {'basics': {'name': 'Tailored Test'}}
        loader_class.return_value.load.return_value = profile
        ai_class.return_value.tailor_profile.return_value = tailored_profile

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, 'data'))
            jd_path = os.path.join(project_dir, 'jd.txt')
            with open(jd_path, 'w', encoding='utf-8') as f:
                f.write('Senior AI Engineer')
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main(jd_path)
            finally:
                os.chdir(previous_dir)

        ai_class.return_value.tailor_profile.assert_called_once_with(profile, 'Senior AI Engineer')
        self.assertEqual(
            generator_class.return_value.generate.call_args_list,
            [
                call(tailored_profile, 'resume.md.j2', 'output/RESUME_tailored.md'),
                call(tailored_profile, 'resume.html.j2', 'output/resume_tailored.html'),
                call(tailored_profile, 'resume_bible.html.j2', 'output/resume_bible_tailored.html'),
            ],
        )


if __name__ == '__main__':
    unittest.main()
