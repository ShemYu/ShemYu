"""HTML-to-PDF rendering and the one-page gate for Japanese 職務経歴書."""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

# Chrome/Chromium PDFs mark each page object as `/Type /Page` and the tree as
# `/Type /Pages`. Counting the former is enough for the one-page gate.
_PAGE_OBJECT = re.compile(rb"/Type\s*/Page(?!s)")


class PdfRenderError(RuntimeError):
    """Raised when a PDF cannot be produced or is not exactly one page."""


def count_pdf_pages(pdf_bytes: bytes) -> int:
    """Return the number of page objects in ``pdf_bytes``."""

    return len(_PAGE_OBJECT.findall(pdf_bytes))


def assert_one_page(pdf_bytes: bytes) -> int:
    """Fail the job when the rendered PDF is not exactly one page.

    The Japanese concise clip is a one-page 職務経歴書. After PDF render,
    callers must invoke this check so a two-page dump cannot ship.
    """

    pages = count_pdf_pages(pdf_bytes)
    if pages != 1:
        raise PdfRenderError(
            f"Japanese 職務経歴書 must be exactly 1 page, got {pages}"
        )
    return pages


def find_chrome() -> str | None:
    for name in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    return None


def render_html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> bytes:
    """Print HTML to PDF with headless Chrome and return the PDF bytes."""

    chrome = find_chrome()
    if chrome is None:
        raise PdfRenderError(
            "A Chrome/Chromium binary is required to render the one-page PDF"
        )

    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    if not html_path.is_file():
        raise PdfRenderError(f"HTML resume not found: {html_path}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if pdf_path.exists():
        pdf_path.unlink()
    command = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--hide-scrollbars",
        "--no-pdf-header-footer",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    # Some Chrome builds write the PDF and then hang in headless mode.
    # Treat a stable output file as success and stop the process.
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 45
    last_size = -1
    stable_reads = 0
    try:
        while time.monotonic() < deadline:
            if pdf_path.is_file():
                size = pdf_path.stat().st_size
                if size > 0 and size == last_size:
                    stable_reads += 1
                    if stable_reads >= 2:
                        break
                else:
                    stable_reads = 0
                    last_size = size
            if process.poll() is not None:
                break
            time.sleep(0.25)
        else:
            process.kill()
            raise PdfRenderError("Chrome timed out while rendering PDF")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        detail = (process.stderr.read() if process.stderr else "") or ""
        raise PdfRenderError(
            f"Chrome failed to render PDF (exit {process.returncode}): {detail.strip()}"
        )
    return pdf_path.read_bytes()


def render_and_assert_one_page(html_path: str | Path, pdf_path: str | Path) -> int:
    """Render ``html_path`` to ``pdf_path`` and fail unless the PDF is one page."""

    pdf_bytes = render_html_to_pdf(html_path, pdf_path)
    return assert_one_page(pdf_bytes)


__all__ = [
    "PdfRenderError",
    "assert_one_page",
    "count_pdf_pages",
    "find_chrome",
    "render_and_assert_one_page",
    "render_html_to_pdf",
]
