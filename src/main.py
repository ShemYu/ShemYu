from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from src.generator import Jinja2Generator
from src.graph.loader import load_graph
from src.i18n import DEFAULT_LANGUAGE, normalize_language
from src.render.adapter import bind_view
from src.render.views import load_view


VIEW_OUTPUTS = (
    ("one-pager", "resume.html.j2", "output/resume.html"),
    ("full", "resume.md.j2", "RESUME.md"),
    ("bible", "resume_bible.html.j2", "output/resume_bible.html"),
    ("github-readme", "readme.md.j2", "README.md"),
)


def main(
    language: str = DEFAULT_LANGUAGE,
    views: Sequence[tuple[str, str, str]] = VIEW_OUTPUTS,
) -> None:
    language = normalize_language(language)
    career_dir = Path("career")
    views_dir = Path("views")
    template_dir = "templates"

    if not career_dir.is_dir():
        raise FileNotFoundError(f"{career_dir} directory not found.")

    graph = load_graph(career_dir)
    generator = Jinja2Generator(template_dir, language=language)
    jobs = []
    for view_id, template_name, output_path in views:
        view = load_view(views_dir / f"{view_id}.yaml")
        if language != view.locale:
            view = view.model_copy(update={"locale": language})
        context = bind_view(graph, view)
        jobs.append((context, template_name, output_path))

    generator.generate_many(jobs)

    if language == "ja" and any(view_id == "one-pager" for view_id, _template, _path in views):
        html_path = next(path for view_id, _template, path in views if view_id == "one-pager")
        pdf_path = str(Path(html_path).with_suffix(".pdf"))
        from src.pdf import render_and_assert_one_page

        pages = render_and_assert_one_page(html_path, pdf_path)
        print(f"One-page check passed: {pdf_path} ({pages} page)")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render resume views from the career wiki/graph."
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        choices=("en", "ja"),
        help="View locale. ja writes a one-page 職務経歴書 (no model).",
    )
    parser.add_argument(
        "--view",
        default=None,
        choices=tuple(item[0] for item in VIEW_OUTPUTS),
        help="Render a single view instead of the canonical set.",
    )
    return parser.parse_args(argv)


def selected_views(view_id: str | None) -> Sequence[tuple[str, str, str]]:
    if view_id is None:
        return VIEW_OUTPUTS
    return tuple(item for item in VIEW_OUTPUTS if item[0] == view_id)


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        main(cli_args.language, selected_views(cli_args.view))
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
