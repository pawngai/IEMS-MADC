"""Documents infrastructure — preview/thumbnail generation.

A ``PreviewGenerator`` produces a small image (typically WebP) used by the
admin browser to render document tiles. Two adapters ship by default:

* ``NoOpPreviewGenerator`` — generation disabled; the preview endpoint
  returns 404. This is the safe production default until image-processing
  dependencies (Pillow for raster, pymupdf for PDF) are vetted.
* ``ImagePassThroughPreviewGenerator`` — for image content types we already
  hold the bytes, so we re-use them as the preview without resizing. Cheap,
  no extra deps, but does not shrink the payload.

Wire a richer generator (e.g. Pillow-based resizer or pymupdf PDF renderer)
by implementing ``PreviewGenerator`` and returning it from ``preview_generator()``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app_platform.config.settings import settings


_IMAGE_PREVIEW_TYPES = frozenset({
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
})


@dataclass(frozen=True, slots=True)
class PreviewResult:
    content: bytes
    media_type: str
    suffix: str  # filename suffix appended after the source filename stem


class PreviewGenerator(Protocol):
    backend_name: str

    def can_generate(self, *, content_type: str | None) -> bool:
        ...

    def generate(
        self, *, content: bytes, content_type: str | None
    ) -> PreviewResult | None:
        ...


class NoOpPreviewGenerator:
    backend_name = "noop"

    def can_generate(self, *, content_type: str | None) -> bool:
        return False

    def generate(self, *, content: bytes, content_type: str | None) -> PreviewResult | None:
        return None


class ImagePassThroughPreviewGenerator:
    """Returns the raw image bytes as the preview, no resizing. Cheap, and
    requires no extra dependencies. PDF/Office types fall through to the
    no-op behavior — wire a real generator if you need those."""

    backend_name = "image-passthrough"

    def can_generate(self, *, content_type: str | None) -> bool:
        return (content_type or "").strip().lower() in _IMAGE_PREVIEW_TYPES

    def generate(self, *, content: bytes, content_type: str | None) -> PreviewResult | None:
        ct = (content_type or "").strip().lower()
        if ct not in _IMAGE_PREVIEW_TYPES:
            return None
        return PreviewResult(content=content, media_type=ct, suffix="_preview")


_DEFAULT_GENERATOR: PreviewGenerator | None = None


def preview_generator() -> PreviewGenerator:
    global _DEFAULT_GENERATOR
    if _DEFAULT_GENERATOR is not None:
        return _DEFAULT_GENERATOR
    backend = (getattr(settings, "document_preview_backend", "") or "").strip().lower()
    if backend == "image-passthrough":
        _DEFAULT_GENERATOR = ImagePassThroughPreviewGenerator()
    else:
        _DEFAULT_GENERATOR = NoOpPreviewGenerator()
    return _DEFAULT_GENERATOR


def set_preview_generator_for_testing(impl: PreviewGenerator | None) -> None:
    global _DEFAULT_GENERATOR
    _DEFAULT_GENERATOR = impl


def preview_filename_for(source_filename: str, *, suffix: str) -> str:
    """Build the deterministic preview filename so the same source always
    points at the same preview blob (no extra metadata round-trip needed)."""
    stem, sep, ext = source_filename.rpartition(".")
    if not sep:
        return f"{source_filename}{suffix}"
    return f"{stem}{suffix}.{ext}"
