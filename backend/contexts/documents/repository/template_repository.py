"""Repository for the ``document_templates`` collection."""
from __future__ import annotations

from typing import Any

from contexts.documents.domain.template import DocumentTemplate, TemplateField

COLLECTION = "document_templates"


class DocumentTemplateRepository:
    def __init__(self, *, db) -> None:
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
        assert_collection_ownership(
            context="documents", collection_name=COLLECTION, write=True,
        )

    async def get(self, template_id: str) -> DocumentTemplate | None:
        if self._db is None:
            return None
        row = await self._db[COLLECTION].find_one({"template_id": template_id}, {"_id": 0})
        if not isinstance(row, dict):
            return None
        return self._to_template(row)

    async def list_active(self) -> list[DocumentTemplate]:
        if self._db is None:
            return []
        cursor = self._db[COLLECTION].find({"active": True}, {"_id": 0})
        rows = await cursor.to_list(length=500)
        return [self._to_template(row) for row in rows if row.get("template_id")]

    async def upsert(self, template: DocumentTemplate, *, active: bool = True) -> None:
        if self._db is None:
            return
        await self._db[COLLECTION].update_one(
            {"template_id": template.template_id},
            {
                "$set": {
                    "template_id": template.template_id,
                    "name": template.name,
                    "document_type": template.document_type,
                    "base_filename": template.base_filename,
                    "content_type": template.content_type,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.type,
                            "required": f.required,
                            "default": f.default,
                            "label": f.label,
                        }
                        for f in template.fields
                    ],
                    "active": active,
                }
            },
            upsert=True,
        )

    @staticmethod
    def _to_template(row: dict[str, Any]) -> DocumentTemplate:
        return DocumentTemplate(
            template_id=str(row.get("template_id")),
            name=str(row.get("name") or row.get("template_id")),
            document_type=str(row.get("document_type") or "ORDER"),
            base_filename=str(row.get("base_filename") or ""),
            content_type=str(row.get("content_type") or "text/plain"),
            fields=[
                TemplateField(
                    name=str(field.get("name")),
                    type=str(field.get("type") or "string"),
                    required=bool(field.get("required")),
                    default=field.get("default"),
                    label=field.get("label"),
                )
                for field in (row.get("fields") or [])
                if isinstance(field, dict) and field.get("name")
            ],
        )
