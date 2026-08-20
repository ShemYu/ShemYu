import argparse
import os
import re
import sys
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


def main(
    target_jd: str | None = None,
    output_name: str = DEFAULT_TAILORED_NAME,
    provider: str | None = None,
    model: str | None = None,
) -> None:
    data_dir = "data"
    template_dir = "templates"

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"{data_dir} directory not found.")
    if target_jd and not os.path.isfile(target_jd):
        raise FileNotFoundError(f"JD file not found: {target_jd}")

    outputs = _tailored_outputs(output_name) if target_jd else CANONICAL_OUTPUTS
    profile = YamlDataLoader(data_dir).load()

    if target_jd:
        jd_text = Path(target_jd).read_text(encoding="utf-8")
        print(f"Tailoring resume for JD: {target_jd}")

        # Keep the deterministic generation path independent from the AI stack.
        from src.ai import build_provider

        profile = build_provider(provider, model).tailor_profile(profile, jd_text)

    Jinja2Generator(template_dir).generate_batch(profile, outputs)


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
        "--provider",
        default=None,
        help="Tailoring provider. Defaults to TAILOR_PROVIDER or openai.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the selected provider's default model.",
    )
    args = parser.parse_args(argv)
    if not args.target_jd:
        if args.output_name != DEFAULT_TAILORED_NAME:
            parser.error("--output-name requires a target_jd file")
        if args.provider is not None:
            parser.error("--provider requires a target_jd file")
        if args.model is not None:
            parser.error("--model requires a target_jd file")
    return args


if __name__ == "__main__":
    try:
        cli_args = parse_args()
        main(cli_args.target_jd, cli_args.output_name, cli_args.provider, cli_args.model)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
