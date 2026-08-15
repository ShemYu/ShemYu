import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jinja2 import StrictUndefined, UndefinedError

from src.generator import Jinja2Generator, format_date


class FormatDateTest(unittest.TestCase):
    def test_formats_full_and_month_dates(self):
        self.assertEqual(format_date('2023-11-01'), 'Nov 2023')
        self.assertEqual(format_date('2024-06'), 'Jun 2024')

    def test_preserves_year_present_and_unknown_values(self):
        self.assertEqual(format_date('2019'), '2019')
        self.assertEqual(format_date('Present'), 'Present')
        self.assertEqual(format_date('Expected 2027'), 'Expected 2027')


class GeneratorSafetyTest(unittest.TestCase):
    def test_strict_undefined_and_html_only_autoescape(self):
        with tempfile.TemporaryDirectory() as template_dir:
            Path(template_dir, 'plain.md.j2').write_text('{{ value }}', encoding='utf-8')
            Path(template_dir, 'page.html.j2').write_text(
                '<a href="{{ url }}">{{ value }}</a>', encoding='utf-8'
            )
            generator = Jinja2Generator(template_dir)

            self.assertIs(generator.env.undefined, StrictUndefined)
            self.assertEqual(generator.render({'value': '<tag>'}, 'plain.md.j2'), '<tag>')
            self.assertEqual(
                generator.render(
                    {'value': '<tag>', 'url': 'https://example.com/?q=<tag>'},
                    'page.html.j2',
                ),
                '<a href="https://example.com/?q=&lt;tag&gt;">&lt;tag&gt;</a>',
            )
            with self.assertRaises(UndefinedError):
                generator.render({}, 'plain.md.j2')

    def test_unsafe_url_is_rejected_before_render(self):
        with tempfile.TemporaryDirectory() as template_dir:
            Path(template_dir, 'page.html.j2').write_text(
                '<a href="{{ basics.url }}">link</a>', encoding='utf-8'
            )
            generator = Jinja2Generator(template_dir)
            with self.assertRaisesRegex(ValueError, 'Unsafe URL'):
                generator.render(
                    {'basics': {'url': 'javascript:alert(1)'}}, 'page.html.j2'
                )

    def test_batch_render_failure_does_not_modify_existing_files(self):
        with tempfile.TemporaryDirectory() as template_dir, tempfile.TemporaryDirectory() as output_dir:
            Path(template_dir, 'ok.md.j2').write_text('new', encoding='utf-8')
            Path(template_dir, 'bad.md.j2').write_text('{{ missing }}', encoding='utf-8')
            first = Path(output_dir, 'first.md')
            second = Path(output_dir, 'second.md')
            first.write_text('old first', encoding='utf-8')
            second.write_text('old second', encoding='utf-8')
            generator = Jinja2Generator(template_dir)

            with self.assertRaises(UndefinedError):
                generator.generate_batch(
                    {},
                    [('ok.md.j2', str(first)), ('bad.md.j2', str(second))],
                )

            self.assertEqual(first.read_text(encoding='utf-8'), 'old first')
            self.assertEqual(second.read_text(encoding='utf-8'), 'old second')

    def test_commit_failure_rolls_back_already_replaced_files(self):
        with tempfile.TemporaryDirectory() as template_dir, tempfile.TemporaryDirectory() as output_dir:
            Path(template_dir, 'first.md.j2').write_text('new first', encoding='utf-8')
            Path(template_dir, 'second.md.j2').write_text('new second', encoding='utf-8')
            first = Path(output_dir, 'first.md')
            second = Path(output_dir, 'second.md')
            first.write_text('old first', encoding='utf-8')
            second.write_text('old second', encoding='utf-8')
            generator = Jinja2Generator(template_dir)
            real_replace = os.replace

            def fail_second(source, destination):
                if destination.endswith('second.md'):
                    raise OSError('simulated commit failure')
                return real_replace(source, destination)

            with patch('src.generator.os.replace', side_effect=fail_second):
                with self.assertRaisesRegex(OSError, 'simulated commit failure'):
                    generator.generate_batch(
                        {},
                        [('first.md.j2', str(first)), ('second.md.j2', str(second))],
                    )

            self.assertEqual(first.read_text(encoding='utf-8'), 'old first')
            self.assertEqual(second.read_text(encoding='utf-8'), 'old second')

    def test_markdown_resume_includes_complete_education_details(self):
        generator = Jinja2Generator('templates')
        output = generator.render(
            {
                'basics': {
                    'name': 'Test User',
                    'label': '',
                    'email': '',
                    'url': '',
                    'profiles': [],
                    'summary': '',
                },
                'work': [],
                'skills': [],
                'certificates': [],
                'publications': [],
                'projects': [],
                'education': [
                    {
                        'institution': 'Example University',
                        'area': 'Computer Science',
                        'studyType': 'Master',
                        'startDate': '2020',
                        'endDate': '2022',
                        'score': '4.0/4',
                        'courses': ['Distributed Systems'],
                        'highlights': ['Research award'],
                    }
                ],
            },
            'resume.md.j2',
        )
        self.assertIn('## Education', output)
        self.assertIn('Master in Computer Science at Example University', output)
        self.assertIn('Score: 4.0/4', output)
        self.assertIn('Courses: Distributed Systems', output)
        self.assertIn('- Research award', output)

    def test_readme_stats_select_github_profile_by_network(self):
        context = {
            'basics': {
                'name': 'Test User',
                'label': '',
                'email': '',
                'summary': '',
                'location': {'city': '', 'region': ''},
                'profiles': [
                    {
                        'network': 'LinkedIn',
                        'username': 'wrong-user',
                        'url': 'https://www.linkedin.com/in/wrong-user',
                    },
                    {
                        'network': 'GitHub',
                        'username': 'right-user',
                        'url': 'https://github.com/right-user',
                    },
                ],
            },
            'work': [{'position': 'Engineer', 'name': 'Company'}],
            'skills': [],
            'publications': [],
        }
        generator = Jinja2Generator('templates')

        rendered = generator.render(context, 'readme.md.j2')

        self.assertIn('username=right-user', rendered)
        self.assertNotIn('username=wrong-user', rendered)

        context['basics']['profiles'] = []
        rendered_without_github = generator.render(context, 'readme.md.j2')
        self.assertNotIn('github-stats-extended', rendered_without_github)


class PublicResumeLayerTest(unittest.TestCase):
    def test_public_resume_templates_drop_evidence(self):
        profile = {
            "work": [
                {
                    "name": "Cookpad",
                    "highlights": ["coverage 40% to 95%"],
                    "evidence": ["15-case / 103-unit internal benchmark"],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as template_dir:
            Path(template_dir, "resume.html.j2").write_text(
                "{% for w in work %}{{ w.highlights[0] }}|{% if w.evidence is defined %}{{ w.evidence }}{% endif %}{% endfor %}",
                encoding="utf-8",
            )
            Path(template_dir, "resume_bible.html.j2").write_text(
                "{% for w in work %}{{ w.evidence[0] }}{% endfor %}",
                encoding="utf-8",
            )
            generator = Jinja2Generator(template_dir)
            public = generator.render(profile, "resume.html.j2")
            bible = generator.render(profile, "resume_bible.html.j2")
        self.assertIn("coverage 40% to 95%", public)
        self.assertNotIn("15-case", public)
        self.assertIn("15-case / 103-unit internal benchmark", bible)


if __name__ == '__main__':
    unittest.main()
