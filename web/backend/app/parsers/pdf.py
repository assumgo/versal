"""Desktop 2.18 PDF reader, with deterministic document cleanup."""
from pathlib import Path

from .extrato import parse_extrato_text
from .types import ParsedStatement


def parse_pdf(path: str | Path) -> ParsedStatement:
    """Read text using the desktop reader order; empty text is not an error."""
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            text = '\n'.join(
                page.extract_text(x_tolerance=1, y_tolerance=3) or ''
                for page in pdf.pages
            )
    except Exception:
        import pymupdf

        with pymupdf.open(path) as document:
            text = '\n'.join(page.get_text() for page in document)
    return parse_extrato_text(text)
