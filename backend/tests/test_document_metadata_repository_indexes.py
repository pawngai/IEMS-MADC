from __future__ import annotations

from pathlib import Path

import pytest

from contexts.documents.repository.metadata_repository import DocumentMetadataRepository


class _FakeCollection:
    def __init__(self) -> None:
        self.created_indexes: list[dict] = []

    async def create_index(self, keys, **kwargs):
        self.created_indexes.append({"keys": keys, **kwargs})
        return "idx"


class _FakeDb:
    def __init__(self) -> None:
        self.collection = _FakeCollection()

    def __getitem__(self, _name: str) -> _FakeCollection:
        return self.collection


@pytest.mark.asyncio
async def test_document_metadata_indexes_use_mongo_compatible_partial_filters() -> None:
    repository = DocumentMetadataRepository(db=_FakeDb(), metadata_dir=Path("."))

    await repository.ensure_indexes()

    assert repository._db.collection.created_indexes == [
        {
            "keys": [("document_id", 1)],
            "unique": True,
            "background": True,
        },
        {
            "keys": [("filename", 1)],
            "unique": True,
            "background": True,
        },
        {
            "keys": [("uploaded_employee_id", 1), ("is_current", 1)],
            "background": True,
        },
        {
            "keys": [("subject_employee_id", 1), ("is_current", 1)],
            "background": True,
            "partialFilterExpression": {
                "subject_employee_id": {"$exists": True, "$type": "string"},
            },
        },
        {
            "keys": [("entity_type", 1), ("entity_id", 1)],
            "background": True,
            "partialFilterExpression": {
                "entity_type": {"$exists": True, "$type": "string"},
                "entity_id": {"$exists": True, "$type": "string"},
            },
        },
        {
            "keys": [("locked_at", -1)],
            "background": True,
            "partialFilterExpression": {
                "locked_at": {"$exists": True, "$type": "string"},
            },
        },
        {
            "keys": [("legal_hold", 1)],
            "background": True,
            "partialFilterExpression": {"legal_hold": True},
        },
        {
            "keys": [("tags", 1)],
            "background": True,
            "partialFilterExpression": {"tags": {"$exists": True, "$type": "array"}},
        },
        {
            "keys": [("expires_at", 1)],
            "background": True,
            "partialFilterExpression": {"expires_at": {"$exists": True, "$type": "string"}},
        },
        {
            "keys": [
                ("original_name", "text"),
                ("document_type", "text"),
                ("category", "text"),
                ("source_context", "text"),
                ("tags", "text"),
                ("uploaded_employee_code", "text"),
                ("subject_employee_code", "text"),
            ],
            "name": "document_metadata_text_idx",
            "background": True,
            "default_language": "english",
        },
        {
            "keys": [("uploaded_at", -1)],
            "background": True,
        },
    ]