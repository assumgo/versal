"""Resolve a local document before any reader can interpret a URL."""
from pathlib import Path


def local_document_path(path: str | Path) -> Path:
    return Path(path).resolve(strict=True)
