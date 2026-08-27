import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from src.generator import Jinja2Generator
from src.i18n import DEFAULT_LANGUAGE, localize_profile, normalize_language
from src.loader import YamlDataLoader


CANONICAL_OUTPUTS = (
    ("resume.md.j2", "RESUME.md"),
    ("resume.html.j2", "output/resume.html"),
    ("resume_bible.html.j2", "output/resume_bible.html"),
    ("readme.md.j2", "README.md"),
)


def main(language: str = DEFAULT_LANGUAGE) -> None:
    data_dir = "data"
    template_dir = "templates"
    language = normalize_language(language)

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"{data_dir} directory not found.")

    profile = YamlDataLoader(data_dir).load()
    # Canonical generation is template clip of locked public highlights.

    if language != "en":
        profile = localize_profile(profile, language)
    Jinja2Generator(template_dir, language=language).generate_batch(
        profile, CANONICAL_OUTPUTS
    )

    if language == "ja":
        html_path = next(
            path for template, path in CANONICAL_OUTPUTS if template == "resume.html.j2"
        )
        pdf_path = str(Path(html_path).with_suffix(".pdf"))
        from src.pdf import render_and_assert_one_page

        pages = render_and_assert_one_page(html_path, pdf_path)
        print(f"One-page check passed: {pdf_path} ({pages} page)")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate canonical resume artifacts from locked YAML highlights."
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        choices=("en", "ja"),
        help=(
            "Render language. ja emits a one-page 職務経歴書 from locked "
            "public highlights (no model)."
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        main(cli_args.language)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
