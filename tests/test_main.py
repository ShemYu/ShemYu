import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.main import (
    DETAILED_VIEW_OUTPUT,
    VIEW_OUTPUTS,
    main,
    parse_args,
    selected_views,
)


class MainTest(unittest.TestCase):
    @patch("src.pdf.render_and_assert_one_page", return_value=1)
    @patch("src.main.Jinja2Generator")
    @patch("src.main.bind_view", return_value={"basics": {"name": "Test"}})
    @patch("src.main.load_view")
    @patch("src.main.load_graph")
    def test_default_generation_renders_each_view(
        self, load_graph, load_view, bind_view, generator_class, pdf_check
    ):
        load_view.return_value = MagicMock(locale="en")
        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "career"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main()
            finally:
                os.chdir(previous_dir)

        generator_class.return_value.generate_many.assert_called_once()
        jobs = generator_class.return_value.generate_many.call_args.args[0]
        self.assertEqual(
            [(template, dest) for _ctx, template, dest in jobs],
            [(template, dest) for _view, template, dest in VIEW_OUTPUTS],
        )
        self.assertEqual(load_graph.call_count, 1)
        self.assertEqual(bind_view.call_count, len(VIEW_OUTPUTS))
        pdf_check.assert_called_once_with(
            "output/resume.html", "output/pdf/shem-yu-resume.pdf"
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

    def test_cli_accepts_single_view(self):
        args = parse_args(["--view", "one-pager"])
        self.assertEqual(args.view, "one-pager")
        self.assertEqual(selected_views("one-pager")[0][0], "one-pager")
        self.assertEqual(len(selected_views("one-pager")), 1)

        detailed = parse_args(["--view", "detailed"])
        self.assertEqual(detailed.view, "detailed")
        self.assertEqual(selected_views("detailed"), (DETAILED_VIEW_OUTPUT,))

    @patch("src.pdf.render_html_to_pdf", return_value=b"/Type /Page")
    @patch("src.main.Jinja2Generator")
    @patch("src.main.bind_view", return_value={"basics": {"name": "Test"}})
    @patch("src.main.load_view")
    @patch("src.main.load_graph")
    def test_detailed_view_renders_its_own_pdf(
        self,
        load_graph,
        load_view,
        bind_view,
        generator_class,
        render_html_to_pdf,
    ):
        load_view.return_value = MagicMock(locale="en")
        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "career"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main(views=selected_views("detailed"))
            finally:
                os.chdir(previous_dir)

        jobs = generator_class.return_value.generate_many.call_args.args[0]
        self.assertEqual(
            [(template, dest) for _ctx, template, dest in jobs],
            [("resume_detailed.html.j2", "output/resume-detailed.html")],
        )
        render_html_to_pdf.assert_called_once_with(
            "output/resume-detailed.html",
            "output/pdf/shem-yu-resume-detailed.pdf",
        )

    @patch("src.pdf.render_and_assert_one_page", return_value=1)
    @patch("src.main.Jinja2Generator")
    @patch("src.main.bind_view", return_value={"basics": {"name": "余顯漁（Shem Yu）"}})
    @patch("src.main.load_view")
    @patch("src.main.load_graph")
    def test_language_ja_runs_one_page_check(
        self, load_graph, load_view, bind_view, generator_class, pdf_check
    ):
        view = MagicMock()
        view.locale = "en"
        view.model_copy.return_value = view
        load_view.return_value = view

        with tempfile.TemporaryDirectory() as project_dir:
            os.makedirs(os.path.join(project_dir, "career"))
            previous_dir = os.getcwd()
            try:
                os.chdir(project_dir)
                main("ja")
            finally:
                os.chdir(previous_dir)

        generator_class.assert_called_once_with("templates", language="ja")
        generator_class.return_value.generate_many.assert_called_once()
        bind_view.assert_called()
        pdf_check.assert_called_once_with(
            "output/resume.html", "output/pdf/shem-yu-resume-ja.pdf"
        )


if __name__ == "__main__":
    unittest.main()
