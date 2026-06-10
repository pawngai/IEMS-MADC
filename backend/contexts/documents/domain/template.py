"""Documents domain — template definition and render rules.

A template captures:
* ``template_id``, ``name``, ``document_type`` — identity + classification
* ``base_filename`` — the stored template body (lives in the standard
  ``StorageBucket.DOCUMENT`` bucket so the standard access path works)
* ``content_type`` — the body's MIME type
* ``fields`` — list of field definitions ``[{"name": str, "type": str,
  "required": bool, "default": str | None}]`` consumed by the renderer

Rendering:
* For text/markdown bodies we substitute ``${field_name}`` placeholders.
* For PDF/Office bodies we pass through unchanged but persist the field
  values on metadata so a downstream office-rendering job can finish the
  fill. The render contract is intentionally narrow — we don't ship a
  Word/PDF form-fill engine in the base codebase.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from string import Template
from typing import Any


_TEXT_RENDER_TYPES = frozenset({"text/plain", "text/markdown", "text/html"})
_VALID_FIELD_TYPES = frozenset({"string", "date", "number", "boolean"})
_FIELD_NAME_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")


@dataclass(slots=True)
class TemplateField:
    name: str
    type: str = "string"
    required: bool = False
    default: str | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        if not _FIELD_NAME_PATTERN.fullmatch(self.name):
            raise ValueError(
                f"Template field name '{self.name}' must be lowercase letters, numbers, or underscores"
            )
        if self.type not in _VALID_FIELD_TYPES:
            raise ValueError(f"Template field type '{self.type}' not allowed")


@dataclass(slots=True)
class DocumentTemplate:
    template_id: str
    name: str
    document_type: str
    base_filename: str
    content_type: str
    fields: list[TemplateField] = field(default_factory=list)


def validate_render_values(template: DocumentTemplate, values: dict[str, Any]) -> dict[str, str]:
    """Cross-check supplied values against the template's field schema and
    return a normalized string-mapped dict ready for substitution."""
    by_name = {f.name: f for f in template.fields}
    unknown = sorted(set(values) - set(by_name))
    if unknown:
        raise ValueError(f"Unknown template fields: {unknown}")

    out: dict[str, str] = {}
    for field_def in template.fields:
        raw = values.get(field_def.name)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if field_def.required:
                raise ValueError(f"Template field '{field_def.name}' is required")
            raw = field_def.default
        if raw is None:
            continue
        out[field_def.name] = str(raw)
    return out


def can_substitute_inline(content_type: str | None) -> bool:
    return (content_type or "").strip().lower() in _TEXT_RENDER_TYPES


def render_text(template_body: bytes, values: dict[str, str]) -> bytes:
    """Substitute ``${field}`` placeholders in a text/markdown body. Uses
    ``string.Template`` so unknown placeholders raise ``KeyError``."""
    text = template_body.decode("utf-8")
    return Template(text).substitute(values).encode("utf-8")
