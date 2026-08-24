import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from src.generator import Jinja2Generator
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


def _named_html_outputs(output_name: str, locale: str) -> Sequence[tuple[str, str]]:
    if not OUTPUT_NAME_PATTERN.fullmatch(output_name):
        raise ValueError(
            "Output name must be 1-64 letters, numbers, underscores, or hyphens "
            "and must start with a letter or number."
        )
    template = "resume_ja.html.j2" if locale == "ja" else "resume.html.j2"
    return ((template, f"output/{output_name}.html"),)


def _format_generated_on(locale: str, today: date | None = None) -> str:
    current = today or date.today()
    if locale == "ja":
        return f"{current.year}年{current.month}月{current.day}日"
    return current.isoformat()


def main(
    target_jd: str | None = None,
    output_name: str = DEFAULT_TAILORED_NAME,
    locale: str = "en",
    select: str | None = None,
    pdf: bool = False,
) -> None:
    data_dir = "data"
    template_dir = "templates"

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"{data_dir} directory not found.")
    if target_jd and not os.path.isfile(target_jd):
        raise FileNotFoundError(f"JD file not found: {target_jd}")
    if target_jd and (locale != "en" or select):
        raise ValueError(
            "Locale and selection presets are deterministic and cannot be "
            "combined with AI job-description tailoring."
        )
    if target_jd:
        _tailored_outputs(output_name)

    profile = YamlDataLoader(data_dir).load()
    selection_meta: dict = {}

    if select:
        from src.select import apply_selection, load_selection

        spec = load_selection(select)
        selection_meta = dict(spec.get("meta") or {})
        profile = apply_selection(profile, spec)
        if output_name == DEFAULT_TAILORED_NAME and selection_meta.get("output_name"):
            output_name = str(selection_meta["output_name"])

    if locale != "en":
        from src.i18n import translate_profile

        profile, untranslated = translate_profile(profile, locale)
        if untranslated:
            print("Untranslated YAML strings left in English:", file=sys.stderr)
            for item in untranslated:
                print(f"  - {item}", file=sys.stderr)

    if select or locale != "en":
        outputs = _named_html_outputs(output_name, locale)
    elif target_jd:
        outputs = _tailored_outputs(output_name)
    else:
        outputs = CANONICAL_OUTPUTS

    if target_jd:
        jd_text = Path(target_jd).read_text(encoding="utf-8")
        print(f"Tailoring resume for JD: {target_jd}")

        # Keep the deterministic generation path independent from the AI stack.
        from src.ai import OpenAIAgentProvider

        profile = OpenAIAgentProvider().tailor_profile(profile, jd_text)

    if select or locale != "en":
        profile["generated_on"] = _format_generated_on(locale)
        profile["selection_meta"] = selection_meta

    Jinja2Generator(template_dir).generate_batch(profile, outputs)

    if pdf:
        html_outputs = [path for _, path in outputs if path.endswith(".html")]
        if not html_outputs:
            raise ValueError("No HTML output is available to convert to PDF.")
        from src.pdf import html_to_pdf

        for html_path in html_outputs:
            pdf_path = str(Path(html_path).with_suffix(".pdf"))
            html_to_pdf(html_path, pdf_path)
            print(f"Successfully generated {pdf_path}")


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
        help="Safe basename for tailored or locale-specific files under output/.",
    )
    parser.add_argument(
        "--locale",
        default="en",
        choices=("en", "ja"),
        help="Render locale. ja uses the Japanese 職務経歴書 template.",
    )
    parser.add_argument(
        "--select",
        help="Deterministic selection preset name under locales/selections/.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also write a PDF next to the generated HTML (requires a CJK font).",
    )
    args = parser.parse_args(argv)
    named_output = args.output_name != DEFAULT_TAILORED_NAME
    if named_output and not (args.target_jd or args.select or args.locale != "en"):
        parser.error("--output-name requires a target_jd file, --select, or --locale")
    if args.pdf and not (args.target_jd or args.select or args.locale != "en"):
        parser.error("--pdf requires a target_jd file, --select, or --locale")
    return args


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        main(
            cli_args.target_jd,
            cli_args.output_name,
            locale=cli_args.locale,
            select=cli_args.select,
            pdf=cli_args.pdf,
        )
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
