import argparse
import os
import re
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
DEFAULT_TAILORED_NAME = "resume_tailored"
OUTPUT_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def _tailored_outputs(output_name: str) -> Sequence[tuple[str, str]]:
    if not OUTPUT_NAME_PATTERN.fullmatch(output_name):
        raise ValueError(
            "Output name must be 1-64 letters, numbers, underscores, or hyphens "
            "and must start with a letter or number."
        )

    return (
        ("resume.md.j2", f"output/tailored/{output_name}.md"),
        ("resume.html.j2", f"output/tailored/{output_name}.html"),
        ("resume_bible.html.j2", f"output/tailored/{output_name}_bible.html"),
    )


def main(
    target_jd: str | None = None,
    output_name: str = DEFAULT_TAILORED_NAME,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    data_dir = "data"
    template_dir = "templates"
    language = normalize_language(language)

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"{data_dir} directory not found.")
    if target_jd and not os.path.isfile(target_jd):
        raise FileNotFoundError(f"JD file not found: {target_jd}")

    outputs = _tailored_outputs(output_name) if target_jd else CANONICAL_OUTPUTS
    profile = YamlDataLoader(data_dir).load()
    # No-JD canonical generation is template clip of locked public highlights.
    # Compose + grounding run only when a job description is supplied.

    if target_jd:
        jd_text = Path(target_jd).read_text(encoding="utf-8")
        print(f"Tailoring resume for JD: {target_jd} (language={language})")

        # Keep the deterministic generation path independent from the AI stack.
        from src.ai import OpenAIAgentProvider

        profile = OpenAIAgentProvider(language=language).tailor_profile(profile, jd_text)

    if language != "en":
        profile = localize_profile(profile, language)
    Jinja2Generator(template_dir, language=language).generate_batch(profile, outputs)

    if language == "ja":
        html_path = next(path for template, path in outputs if template == "resume.html.j2")
        pdf_path = str(Path(html_path).with_suffix(".pdf"))
        from src.pdf import render_and_assert_one_page

        pages = render_and_assert_one_page(html_path, pdf_path)
        print(f"One-page check passed: {pdf_path} ({pages} page)")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate canonical or job-tailored resume artifacts."
    )
    parser.add_argument(
        "target_jd",
        nargs="?",
        help="Path to a job description. Omit it for deterministic canonical output.",
    )
    parser.add_argument(
        "--output-name",
        default=DEFAULT_TAILORED_NAME,
        help="Safe basename for tailored files under output/.",
    )
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        choices=("en", "ja"),
        help="Render language. ja emits a one-page 職務経歴書 from the same concise template.",
    )
    args = parser.parse_args(argv)
    if not args.target_jd and args.output_name != DEFAULT_TAILORED_NAME:
        parser.error("--output-name requires a target_jd file")
    return args


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        main(cli_args.target_jd, cli_args.output_name, cli_args.language)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
