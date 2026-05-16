"""Render-QA — convert DOCX to PDF via LibreOffice headless and count pages.

Anna 2026-05-13 Round 2 (P0-1): the 5-page layout goal can only be enforced
by an actual render-and-count loop. Without `soffice`, the 5-page assertion
is a wish, not a guarantee. Install LibreOffice on the dev machine:

    brew install --cask libreoffice

The module degrades gracefully when soffice is missing — `find_soffice()`
returns `None` and tests should `pytest.skip()` instead of failing.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


# Common install paths on macOS / Linux. `shutil.which` finds CLI installs;
# the explicit paths catch the macOS .app bundle which puts soffice deep inside.
_CANDIDATE_PATHS = (
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice",
    "/usr/bin/libreoffice",
    "/usr/bin/soffice",
)


def find_soffice() -> str | None:
    """Return the path to soffice/libreoffice, or None if not installed."""
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    for p in _CANDIDATE_PATHS:
        if Path(p).exists() and os.access(p, os.X_OK):
            return p
    return None


def render_to_pdf(docx_path: Path, out_dir: Path | None = None,
                  *, soffice: str | None = None) -> Path:
    """Convert a .docx file to PDF using LibreOffice headless.

    Returns the path to the generated PDF (same basename as the docx).
    Raises RuntimeError if soffice is missing or conversion fails.
    """
    bin_path = soffice or find_soffice()
    if not bin_path:
        raise RuntimeError(
            "LibreOffice nicht gefunden. Installation: brew install --cask libreoffice"
        )

    out_dir = out_dir or docx_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            bin_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(docx_path),
        ],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"soffice PDF-Konvertierung fehlgeschlagen "
            f"(rc={result.returncode}):\n{result.stderr}"
        )

    pdf_path = out_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        raise RuntimeError(
            f"PDF wurde nicht erzeugt, obwohl soffice rc=0 zurückgab: {pdf_path}"
        )
    return pdf_path


def count_pages(pdf_path: Path) -> int:
    """Count pages in a PDF using pypdf."""
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    return len(reader.pages)
