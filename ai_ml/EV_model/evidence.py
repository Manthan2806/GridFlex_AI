"""Cross-platform evidence hashing for EV experiment text files."""

from __future__ import annotations

import hashlib
from pathlib import Path


def canonical_text_bytes(path: Path) -> bytes:
    """Return UTF-8 bytes with a single canonical newline representation."""
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def canonical_sha256(path: Path) -> str:
    """Hash text content independently of Windows or Unix line endings."""
    return hashlib.sha256(canonical_text_bytes(path)).hexdigest()


def file_sha256(path: Path) -> str:
    """Hash an arbitrary file byte-for-byte, including binary artifacts."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
