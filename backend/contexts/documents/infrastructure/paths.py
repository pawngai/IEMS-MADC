"""Documents infrastructure — shared path constants.

All document storage paths are defined here so that test monkeypatching
on either this module or the ``service`` facade propagates consistently.
"""
from __future__ import annotations

from pathlib import Path

from app_platform.config.settings import settings

UPLOAD_DIR = Path(settings.uploads_dir)
PHOTO_DIR = UPLOAD_DIR / "photos"
SIGNATURE_DIR = UPLOAD_DIR / "signatures"
DOCUMENT_DIR = UPLOAD_DIR / "documents"
DOCUMENT_META_DIR = DOCUMENT_DIR / "_meta"
ARCHIVE_DIR = UPLOAD_DIR / "archive"
PREVIEW_DIR = UPLOAD_DIR / "previews"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENT_META_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
