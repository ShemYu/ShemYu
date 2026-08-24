"""Render a resume HTML file to PDF using a CJK-capable font."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


CJK_FONT_CANDIDATES = (
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"),
    Path("/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf"),
    Path("/usr/share/fonts/opentype/noto/NotoSansJP-Regular.otf"),
)
CJK_FONT_NAMES = (
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "Source Han Sans JP",
    "Source Han Sans",
)


def find_cjk_font_file() -> Path | None:
    for path in CJK_FONT_CANDIDATES:
        if path.is_file():
            return path
    return None


def require_cjk_font() -> Path:
    font = find_cjk_font_file()
    if font is None:
        raise RuntimeError(
            "A CJK-capable font is required for Japanese PDFs. "
            "Install Noto Sans CJK (Debian/Ubuntu: fonts-noto-cjk) "
            "or Noto Sans JP / Source Han Sans."
        )
    return font


def _chrome_executable() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _write_pdf_with_chrome(html_path: Path, pdf_path: Path) -> None:
    chrome = _chrome_executable()
    if chrome is None:
        raise RuntimeError("chrome")
    html_uri = html_path.resolve().as_uri()
    command = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-pdf-header-footer",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={pdf_path.resolve()}",
        html_uri,
    ]
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=45
    )
    if result.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError(
            "Chrome PDF export failed: "
            f"{result.stderr.strip() or result.stdout.strip() or result.returncode}"
        )


def _write_pdf_with_weasyprint(html_path: Path, pdf_path: Path, font_file: Path) -> None:
    try:
        from weasyprint import CSS, HTML
    except ImportError as error:
        raise RuntimeError("weasyprint") from error

    font_css = CSS(
        string=(
            "@font-face {"
            '  font-family: "Noto Sans JP";'
            f'  src: url("{font_file.resolve().as_uri()}");'
            "  font-weight: 400;"
            "}"
            "@font-face {"
            '  font-family: "Noto Sans CJK JP";'
            f'  src: url("{font_file.resolve().as_uri()}");'
            "  font-weight: 400;"
            "}"
        )
    )
    HTML(filename=str(html_path)).write_pdf(str(pdf_path), stylesheets=[font_css])


def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> Path:
    """Write a PDF beside the HTML, embedding a CJK font via Chrome or WeasyPrint."""

    source = Path(html_path)
    destination = Path(pdf_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    font_file = require_cjk_font()
    destination.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    try:
        _write_pdf_with_weasyprint(source, destination, font_file)
        return destination
    except RuntimeError as error:
        errors.append(str(error))
    if _chrome_executable():
        try:
            _write_pdf_with_chrome(source, destination)
            return destination
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            errors.append(str(error))

    raise RuntimeError(
        "Could not render a Japanese PDF. Install Google Chrome/Chromium "
        "or `uv sync --extra pdf` (WeasyPrint), and keep a Noto CJK font "
        f"installed. Details: {'; '.join(errors)}"
    )


__all__ = [
    "CJK_FONT_NAMES",
    "find_cjk_font_file",
    "html_to_pdf",
    "require_cjk_font",
]
