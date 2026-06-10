from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from app_platform.db.atomic import call_with_optional_session

COLLECTION = "document_metadata"


class DocumentMetadataRepository:
    _indexed_db_keys: set[int] = set()

    def __init__(self, *, db=None, metadata_dir: Path):
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
        self._metadata_dir = metadata_dir
        assert_collection_ownership(
            context="documents", collection_name=COLLECTION, write=True,
        )

    async def ensure_indexes(self) -> None:
        if self._db is None:
            return

        db_key = id(self._db)
        if db_key in self._indexed_db_keys:
            return

        collection = self._db[COLLECTION]
        if not hasattr(collection, "create_index"):
            return

        await collection.create_index(
            [("document_id", 1)],
            unique=True,
            background=True,
        )
        await collection.create_index(
            [("filename", 1)],
            unique=True,
            background=True,
        )
        await collection.create_index(
            [("uploaded_employee_id", 1), ("is_current", 1)],
            background=True,
        )
        await collection.create_index(
            [("subject_employee_id", 1), ("is_current", 1)],
            background=True,
            partialFilterExpression={"subject_employee_id": {"$exists": True, "$type": "string"}},
        )
        await collection.create_index(
            [("entity_type", 1), ("entity_id", 1)],
            background=True,
            partialFilterExpression={
                "entity_type": {"$exists": True, "$type": "string"},
                "entity_id": {"$exists": True, "$type": "string"},
            },
        )
        await collection.create_index(
            [("locked_at", -1)],
            background=True,
            partialFilterExpression={"locked_at": {"$exists": True, "$type": "string"}},
        )
        await collection.create_index(
            [("legal_hold", 1)],
            background=True,
            partialFilterExpression={"legal_hold": True},
        )
        await collection.create_index(
            [("tags", 1)],
            background=True,
            partialFilterExpression={"tags": {"$exists": True, "$type": "array"}},
        )
        await collection.create_index(
            [("expires_at", 1)],
            background=True,
            partialFilterExpression={"expires_at": {"$exists": True, "$type": "string"}},
        )
        # Single text index for richer search across the obvious queryable
        # fields. ``$text`` queries with this index will outrank pure regex
        # for multi-token searches. Wrap in try/except so deployments where
        # ``textIndexVersion`` features aren't available don't crash startup.
        try:
            await collection.create_index(
                [
                    ("original_name", "text"),
                    ("document_type", "text"),
                    ("category", "text"),
                    ("source_context", "text"),
                    ("tags", "text"),
                    ("uploaded_employee_code", "text"),
                    ("subject_employee_code", "text"),
                ],
                name="document_metadata_text_idx",
                background=True,
                default_language="english",
            )
        except Exception:
            # Re-creating a text index with a different field set raises in
            # Mongo. The recovery path is to drop and recreate, but at runtime
            # we just log+skip so a startup that already has the index
            # survives.
            pass
        await collection.create_index(
            [("uploaded_at", -1)],
            background=True,
        )

        self._indexed_db_keys.add(db_key)

    async def get(self, filename: str, *, session=None) -> dict[str, Any] | None:
        if self._db is None:
            return self._get_local(filename)
        await self.ensure_indexes()
        data = await call_with_optional_session(
            self._db[COLLECTION].find_one,
            {"filename": filename},
            {"_id": 0},
            session=session,
        )
        return self._normalize_metadata(filename, data) if isinstance(data, dict) else None

    async def get_by_document_id(self, document_id: str, *, session=None) -> dict[str, Any] | None:
        normalized_document_id = self._normalize_optional_string(document_id)
        if not normalized_document_id:
            return None

        if self._db is None:
            for metadata in self._iter_local_metadata():
                if metadata.get("document_id") == normalized_document_id:
                    return metadata
            return None

        await self.ensure_indexes()
        data = await call_with_optional_session(
            self._db[COLLECTION].find_one,
            {"document_id": normalized_document_id},
            {"_id": 0},
            session=session,
        )
        return (
            self._normalize_metadata(str(data.get("filename")), data)
            if isinstance(data, dict) and data.get("filename")
            else None
        )

    async def upsert(self, filename: str, metadata: dict[str, Any], *, session=None) -> None:
        payload = self._normalize_metadata(filename, metadata)
        if self._db is None:
            self._upsert_local(filename, payload)
            return
        await self.ensure_indexes()
        await call_with_optional_session(
            self._db[COLLECTION].update_one,
            {"filename": filename},
            {"$set": payload},
            upsert=True,
            session=session,
        )

    async def delete(self, filename: str, *, session=None) -> None:
        if self._db is None:
            self._delete_local(filename)
            return
        await self.ensure_indexes()
        await call_with_optional_session(
            self._db[COLLECTION].delete_one,
            {"filename": filename},
            session=session,
        )

    async def get_many(self, filenames: list[str]) -> dict[str, dict[str, Any]]:
        if not filenames:
            return {}
        if self._db is None:
            return {
                filename: metadata
                for filename in filenames
                if (metadata := self._get_local(filename)) is not None
            }

        await self.ensure_indexes()
        cursor = self._db[COLLECTION].find(
            {"filename": {"$in": filenames}},
            {"_id": 0},
        )
        items = await cursor.to_list(length=len(filenames))
        return {
            str(item.get("filename")): self._normalize_metadata(str(item.get("filename")), item)
            for item in items
            if isinstance(item, dict) and item.get("filename")
        }

    async def has_successor(self, document_id: str) -> bool:
        normalized_document_id = self._normalize_optional_string(document_id)
        if not normalized_document_id:
            return False

        if self._db is None:
            return any(
                metadata.get("supersedes_document_id") == normalized_document_id
                for metadata in self._iter_local_metadata()
            )

        await self.ensure_indexes()
        return bool(
            await self._db[COLLECTION].count_documents(
                {"supersedes_document_id": normalized_document_id},
                limit=1,
            )
        )

    async def list_documents(
        self,
        *,
        owner_field: str | None = None,
        owner_value: str | None = None,
        query: str | None = None,
		uploader_query: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        document_type: str | None = None,
        category: str | None = None,
        source_context: str | None = None,
        is_locked: bool | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        tags_any: list[str] | None = None,
        tags_all: list[str] | None = None,
        text_query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        if self._db is None:
            items = self._filter_items(
                self._iter_local_metadata(),
                owner_field=owner_field,
                owner_value=owner_value,
                query=query,
				uploader_query=uploader_query,
                entity_type=entity_type,
                entity_id=entity_id,
                document_type=document_type,
                category=category,
                source_context=source_context,
                is_locked=is_locked,
                date_from=date_from,
                date_to=date_to,
                tags_any=tags_any,
                tags_all=tags_all,
                text_query=text_query,
            )
            total = len(items)
            return items[offset : offset + limit], total

        await self.ensure_indexes()
        mongo_query: dict[str, Any] = {}
        if owner_field and owner_value:
            mongo_query[owner_field] = owner_value
        if entity_type:
            mongo_query["entity_type"] = entity_type
        if entity_id:
            mongo_query["entity_id"] = entity_id
        if document_type:
            mongo_query["document_type"] = document_type
        if category:
            mongo_query["category"] = category
        if source_context:
            mongo_query["source_context"] = source_context
        if is_locked is not None:
            mongo_query["is_locked"] = is_locked
        if tags_any:
            mongo_query["tags"] = {"$in": list(tags_any)}
        if tags_all:
            existing = mongo_query.get("tags")
            if isinstance(existing, dict):
                existing["$all"] = list(tags_all)
            else:
                mongo_query["tags"] = {"$all": list(tags_all)}
        if text_query and text_query.strip():
            mongo_query["$text"] = {"$search": text_query.strip()}
        if date_from or date_to:
            uploaded_at_query: dict[str, Any] = {}
            if date_from:
                uploaded_at_query["$gte"] = date_from
            if date_to:
                uploaded_at_query["$lte"] = date_to
            mongo_query["uploaded_at"] = uploaded_at_query
        compound_clauses: list[dict[str, Any]] = []
        if query:
            escaped = re.escape(query)
            compound_clauses.append(
                {
                    "$or": [
                        {"filename": {"$regex": escaped, "$options": "i"}},
                        {"original_name": {"$regex": escaped, "$options": "i"}},
                    ]
                }
            )
        if uploader_query:
            escaped_uploader = re.escape(uploader_query)
            compound_clauses.append(
                {
                    "$or": [
                        {"uploaded_employee_id": {"$regex": escaped_uploader, "$options": "i"}},
                        {"uploaded_employee_code": {"$regex": escaped_uploader, "$options": "i"}},
                        {"uploaded_by_user_id": {"$regex": escaped_uploader, "$options": "i"}},
                    ]
                }
            )
        if len(compound_clauses) == 1:
            mongo_query.update(compound_clauses[0])
        elif compound_clauses:
            mongo_query["$and"] = compound_clauses

        collection = self._db[COLLECTION]
        total = int(await collection.count_documents(mongo_query))
        if text_query and text_query.strip():
            cursor = (
                collection.find(
                    mongo_query,
                    {"_id": 0, "score": {"$meta": "textScore"}},
                )
                .sort([("score", {"$meta": "textScore"}), ("uploaded_at", -1)])
                .skip(offset)
                .limit(limit)
            )
        else:
            cursor = collection.find(mongo_query, {"_id": 0}).sort("uploaded_at", -1).skip(offset).limit(limit)
        items = await cursor.to_list(length=limit)
        return [
            self._normalize_metadata(str(item.get("filename")), item)
            for item in items
            if isinstance(item, dict) and item.get("filename")
        ], total

    async def list_by_employee_id(
        self,
        employee_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        current_only: bool = False,
    ) -> list[dict[str, Any]]:
        normalized_employee_id = self._normalize_optional_string(employee_id)
        if not normalized_employee_id:
            return []

        if self._db is None:
            items = [
                metadata
                for metadata in self._iter_local_metadata()
                if metadata.get("uploaded_employee_id") == normalized_employee_id
            ]
            if current_only:
                items = [item for item in items if item.get("is_current") is True]
            return items[offset : offset + limit]

        await self.ensure_indexes()
        query: dict[str, Any] = {"uploaded_employee_id": normalized_employee_id}
        if current_only:
            query["is_current"] = True
        cursor = self._db[COLLECTION].find(query, {"_id": 0}).sort("uploaded_at", -1).skip(offset).limit(limit)
        items = await cursor.to_list(length=limit)
        return [
            self._normalize_metadata(str(item.get("filename")), item)
            for item in items
            if isinstance(item, dict) and item.get("filename")
        ]

    async def list_version_chain(self, document_id: str) -> list[dict[str, Any]]:
        """Return the full version history for ``document_id`` sorted by
        ``version_number`` ascending. Walks both directions of the chain:
        backward via ``supersedes_document_id`` and forward via successors
        that point at any node in the chain. Local fallback iterates all
        rows; the Mongo path uses two indexed lookups per traversal step."""
        normalized = self._normalize_optional_string(document_id)
        if not normalized:
            return []

        if self._db is None:
            return self._version_chain_local(normalized)

        await self.ensure_indexes()
        seen: dict[str, dict[str, Any]] = {}

        async def _load(doc_id: str) -> dict[str, Any] | None:
            if doc_id in seen:
                return seen[doc_id]
            row = await self._db[COLLECTION].find_one({"document_id": doc_id}, {"_id": 0})
            if not isinstance(row, dict):
                return None
            normalized_row = self._normalize_metadata(str(row.get("filename")), row)
            seen[doc_id] = normalized_row
            return normalized_row

        current = await _load(normalized)
        # Walk backwards along ``supersedes_document_id``.
        while current and current.get("supersedes_document_id"):
            prev_id = str(current["supersedes_document_id"])
            current = await _load(prev_id)

        # Walk forwards via successor lookups.
        frontier = [normalized] + list(seen.keys())
        visited_successor_lookup: set[str] = set()
        while frontier:
            doc_id = frontier.pop()
            if doc_id in visited_successor_lookup:
                continue
            visited_successor_lookup.add(doc_id)
            cursor = self._db[COLLECTION].find(
                {"supersedes_document_id": doc_id}, {"_id": 0}
            )
            async for row in cursor:
                if not isinstance(row, dict):
                    continue
                row_id = str(row.get("document_id") or "").strip()
                if not row_id or row_id in seen:
                    continue
                normalized_row = self._normalize_metadata(str(row.get("filename")), row)
                seen[row_id] = normalized_row
                frontier.append(row_id)

        return sorted(
            seen.values(),
            key=lambda r: int(r.get("version_number") or 1),
        )

    def _version_chain_local(self, document_id: str) -> list[dict[str, Any]]:
        items = self._iter_local_metadata()
        by_doc_id = {
            str(row.get("document_id") or ""): row
            for row in items
            if row.get("document_id")
        }
        if document_id not in by_doc_id:
            return []
        # Walk backward
        chain: dict[str, dict[str, Any]] = {}
        cursor = by_doc_id[document_id]
        while cursor:
            chain[str(cursor.get("document_id"))] = cursor
            prev_id = str(cursor.get("supersedes_document_id") or "")
            if not prev_id or prev_id in chain:
                break
            cursor = by_doc_id.get(prev_id)
        # Walk forward — find any rows that supersede something in the chain
        added = True
        while added:
            added = False
            for row in items:
                prev_id = str(row.get("supersedes_document_id") or "")
                doc_id = str(row.get("document_id") or "")
                if prev_id in chain and doc_id and doc_id not in chain:
                    chain[doc_id] = row
                    added = True
        return sorted(chain.values(), key=lambda r: int(r.get("version_number") or 1))

    async def list_by_entity(
        self,
        *,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        normalized_entity_type = self._normalize_optional_string(entity_type, upper=True)
        normalized_entity_id = self._normalize_optional_string(entity_id)
        if not normalized_entity_type or not normalized_entity_id:
            return []

        if self._db is None:
            items = [
                metadata
                for metadata in self._iter_local_metadata()
                if metadata.get("entity_type") == normalized_entity_type
                and metadata.get("entity_id") == normalized_entity_id
            ]
            return items[offset : offset + limit]

        await self.ensure_indexes()
        cursor = (
            self._db[COLLECTION]
            .find(
                {"entity_type": normalized_entity_type, "entity_id": normalized_entity_id},
                {"_id": 0},
            )
            .sort("uploaded_at", -1)
            .skip(offset)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        return [
            self._normalize_metadata(str(item.get("filename")), item)
            for item in items
            if isinstance(item, dict) and item.get("filename")
        ]

    def _document_meta_path(self, filename: str) -> Path:
        return self._metadata_dir / f"{filename}.json"

    def _get_local(self, filename: str) -> dict[str, Any] | None:
        path = self._document_meta_path(filename)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            if isinstance(data, dict):
                return self._normalize_metadata(filename, data)
        except Exception:
            return None
        return None

    def _upsert_local(self, filename: str, metadata: dict[str, Any]) -> None:
        self._metadata_dir.mkdir(parents=True, exist_ok=True)
        with open(self._document_meta_path(filename), "w", encoding="utf-8") as file_handle:
            json.dump(metadata, file_handle, ensure_ascii=False)

    def _delete_local(self, filename: str) -> None:
        path = self._document_meta_path(filename)
        if path.exists():
            path.unlink()

    def _iter_local_metadata(self) -> list[dict[str, Any]]:
        if not self._metadata_dir.exists():
            return []

        items: list[dict[str, Any]] = []
        for path in self._metadata_dir.glob("*.json"):
            filename = path.stem
            if metadata := self._get_local(filename):
                items.append(metadata)
        items.sort(key=lambda item: str(item.get("uploaded_at") or ""), reverse=True)
        return items

    def _normalize_metadata(self, filename: str, metadata: dict[str, Any] | None) -> dict[str, Any]:
        data = dict(metadata or {})
        normalized_filename = self._normalize_optional_string(data.get("filename") or filename)
        payload: dict[str, Any] = {**data}
        payload["document_id"] = self._normalize_optional_string(data.get("document_id") or normalized_filename)
        payload["filename"] = normalized_filename
        payload["original_name"] = self._normalize_optional_string(data.get("original_name") or normalized_filename)
        payload["content_type"] = self._normalize_optional_string(data.get("content_type"))
        payload["file_size"] = self._normalize_int(data.get("file_size"), default=0, minimum=0)
        payload["uploaded_by_user_id"] = self._normalize_optional_string(data.get("uploaded_by_user_id"))
        # ``uploaded_by`` was a legacy alias for ``uploaded_by_user_id``. The
        # alias is no longer written; existing rows are reconciled by the
        # ``drop_uploaded_by_alias`` migration. Drop any inbound alias from
        # the payload so later upsert calls don't re-introduce it.
        payload.pop("uploaded_by", None)
        payload["uploaded_employee_id"] = self._normalize_optional_string(data.get("uploaded_employee_id"))
        payload["uploaded_employee_code"] = self._normalize_optional_string(data.get("uploaded_employee_code"))
        payload["subject_employee_id"] = self._normalize_optional_string(data.get("subject_employee_id"))
        payload["subject_employee_code"] = self._normalize_optional_string(data.get("subject_employee_code"))
        payload["uploaded_at"] = self._normalize_optional_string(data.get("uploaded_at"))
        payload["entity_type"] = self._normalize_optional_string(data.get("entity_type"), upper=True)
        payload["entity_id"] = self._normalize_optional_string(data.get("entity_id"))
        payload["document_type"] = self._normalize_optional_string(data.get("document_type"), upper=True)
        payload["category"] = self._normalize_optional_string(data.get("category"), upper=True)
        payload["source_context"] = self._normalize_optional_string(data.get("source_context"), lower=True)
        payload["is_locked"] = bool(data.get("is_locked") or data.get("locked_at") or data.get("lock_reason"))
        payload["locked_at"] = self._normalize_optional_string(data.get("locked_at"))
        payload["lock_reason"] = self._normalize_optional_string(data.get("lock_reason"))
        payload["locked_by_request_id"] = self._normalize_optional_string(data.get("locked_by_request_id"))
        payload["locked_status"] = self._normalize_optional_string(data.get("locked_status"), upper=True)
        payload["legal_hold"] = bool(data.get("legal_hold"))
        payload["legal_hold_reason"] = self._normalize_optional_string(data.get("legal_hold_reason"))
        payload["legal_hold_applied_at"] = self._normalize_optional_string(data.get("legal_hold_applied_at"))
        payload["legal_hold_applied_by_user_id"] = self._normalize_optional_string(
            data.get("legal_hold_applied_by_user_id")
        )
        payload["archived_at"] = self._normalize_optional_string(data.get("archived_at"))
        payload["archived_to_bucket"] = self._normalize_optional_string(data.get("archived_to_bucket"))
        payload["retention_policy_key"] = self._normalize_optional_string(data.get("retention_policy_key"))
        payload["scan_status"] = self._normalize_optional_string(data.get("scan_status"), upper=True)
        payload["scan_threat_name"] = self._normalize_optional_string(data.get("scan_threat_name"))
        payload["scan_completed_at"] = self._normalize_optional_string(data.get("scan_completed_at"))
        payload["tags"] = self._normalize_tag_list(data.get("tags"))
        payload["preview_filename"] = self._normalize_optional_string(data.get("preview_filename"))
        payload["expires_at"] = self._normalize_optional_string(data.get("expires_at"))
        payload["expiry_notified_stages"] = self._normalize_tag_list(data.get("expiry_notified_stages"))
        payload["version_number"] = self._normalize_int(data.get("version_number"), default=1, minimum=1)
        payload["is_current"] = bool(data.get("is_current", True))
        payload["supersedes_document_id"] = self._normalize_optional_string(data.get("supersedes_document_id"))
        return payload

    def _filter_items(
        self,
        items: list[dict[str, Any]],
        *,
        owner_field: str | None,
        owner_value: str | None,
        query: str | None,
		uploader_query: str | None,
        entity_type: str | None,
        entity_id: str | None,
        document_type: str | None,
        category: str | None,
        source_context: str | None,
        is_locked: bool | None,
        date_from: str | None,
        date_to: str | None,
        tags_any: list[str] | None = None,
        tags_all: list[str] | None = None,
        text_query: str | None = None,
    ) -> list[dict[str, Any]]:
        filtered = list(items)
        if owner_field and owner_value:
            filtered = [item for item in filtered if item.get(owner_field) == owner_value]
        if entity_type:
            filtered = [item for item in filtered if item.get("entity_type") == entity_type]
        if entity_id:
            filtered = [item for item in filtered if item.get("entity_id") == entity_id]
        if document_type:
            filtered = [item for item in filtered if item.get("document_type") == document_type]
        if category:
            filtered = [item for item in filtered if item.get("category") == category]
        if source_context:
            filtered = [item for item in filtered if item.get("source_context") == source_context]
        if is_locked is not None:
            filtered = [item for item in filtered if bool(item.get("is_locked")) is is_locked]
        if date_from:
            filtered = [item for item in filtered if str(item.get("uploaded_at") or "") >= date_from]
        if date_to:
            filtered = [item for item in filtered if str(item.get("uploaded_at") or "") <= date_to]
        if query:
            lowered = query.lower()
            filtered = [
                item
                for item in filtered
                if lowered in str(item.get("filename") or "").lower()
                or lowered in str(item.get("original_name") or "").lower()
            ]
        if uploader_query:
            lowered_uploader = uploader_query.lower()
            filtered = [
                item
                for item in filtered
                if lowered_uploader in str(item.get("uploaded_employee_id") or "").lower()
                or lowered_uploader in str(item.get("uploaded_employee_code") or "").lower()
                or lowered_uploader in str(item.get("uploaded_by_user_id") or "").lower()
            ]
        if tags_any:
            wanted_any = {t.lower() for t in tags_any if t}
            filtered = [item for item in filtered if wanted_any & set(item.get("tags") or [])]
        if tags_all:
            wanted_all = {t.lower() for t in tags_all if t}
            filtered = [item for item in filtered if wanted_all.issubset(set(item.get("tags") or []))]
        if text_query and text_query.strip():
            tokens = [tok for tok in text_query.strip().lower().split() if tok]
            def _matches(item: dict[str, Any]) -> bool:
                hay = " ".join(
                    str(item.get(k) or "")
                    for k in (
                        "original_name", "document_type", "category", "source_context",
                        "uploaded_employee_code", "subject_employee_code",
                    )
                ) + " " + " ".join(item.get("tags") or [])
                hay = hay.lower()
                return any(tok in hay for tok in tokens)
            filtered = [item for item in filtered if _matches(item)]
        return filtered

    @staticmethod
    def _normalize_tag_list(value: Any) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return []
        seen: set[str] = set()
        out: list[str] = []
        for raw in value:
            if raw is None:
                continue
            text = str(raw).strip().lower()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        out.sort()
        return out

    @staticmethod
    def _normalize_optional_string(value: Any, *, upper: bool = False, lower: bool = False) -> str | None:
        text = str(value).strip() if value is not None else ""
        if not text:
            return None
        if upper:
            return text.upper()
        if lower:
            return text.lower()
        return text

    @staticmethod
    def _normalize_int(value: Any, *, default: int, minimum: int) -> int:
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            return default
        return normalized if normalized >= minimum else default