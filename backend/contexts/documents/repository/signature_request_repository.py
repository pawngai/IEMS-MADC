"""Repository for the ``document_signature_requests`` collection."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from contexts.documents.domain.signature_request import (
    SIGNATURE_STATUS_PENDING,
    SignatureRequest,
    Signer,
)

COLLECTION = "document_signature_requests"


class SignatureRequestRepository:
    _indexed_db_keys: set[int] = set()

    def __init__(self, *, db) -> None:
        from app_platform.domain_separation.data_ownership import assert_collection_ownership

        self._db = db
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
        await collection.create_index([("request_id", 1)], unique=True, background=True)
        await collection.create_index([("document_id", 1)], background=True)
        await collection.create_index(
            [("signers.employee_id", 1), ("status", 1)],
            background=True,
        )
        self._indexed_db_keys.add(db_key)

    async def upsert(self, request: SignatureRequest) -> None:
        if self._db is None:
            return
        await self.ensure_indexes()
        await self._db[COLLECTION].update_one(
            {"request_id": request.request_id},
            {"$set": _to_doc(request)},
            upsert=True,
        )

    async def get(self, request_id: str) -> SignatureRequest | None:
        if self._db is None:
            return None
        await self.ensure_indexes()
        row = await self._db[COLLECTION].find_one({"request_id": request_id}, {"_id": 0})
        return _from_doc(row) if isinstance(row, dict) else None

    async def list_pending_for_signer(self, employee_id: str) -> list[SignatureRequest]:
        if self._db is None:
            return []
        await self.ensure_indexes()
        cursor = self._db[COLLECTION].find(
            {
                "status": SIGNATURE_STATUS_PENDING,
                "signers.employee_id": employee_id,
            },
            {"_id": 0},
        )
        rows = await cursor.to_list(length=500)
        out: list[SignatureRequest] = []
        for row in rows:
            req = _from_doc(row)
            if req is None:
                continue
            # Only include if it's actually this signer's turn.
            idx = req.current_signer_index()
            if idx is not None and req.signers[idx].employee_id == employee_id:
                out.append(req)
        return out


def _to_doc(request: SignatureRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "document_id": request.document_id,
        "filename": request.filename,
        "status": request.status,
        "issuer_user_id": request.issuer_user_id,
        "issuer_employee_id": request.issuer_employee_id,
        "created_at": request.created_at,
        "deadline_at": request.deadline_at,
        "completed_at": request.completed_at,
        "signers": [asdict(s) for s in request.signers],
    }


def _from_doc(row: dict[str, Any] | None) -> SignatureRequest | None:
    if not isinstance(row, dict):
        return None
    return SignatureRequest(
        request_id=str(row.get("request_id") or ""),
        document_id=str(row.get("document_id") or ""),
        filename=str(row.get("filename") or ""),
        status=str(row.get("status") or SIGNATURE_STATUS_PENDING),
        issuer_user_id=row.get("issuer_user_id"),
        issuer_employee_id=row.get("issuer_employee_id"),
        created_at=str(row.get("created_at") or ""),
        deadline_at=row.get("deadline_at"),
        completed_at=row.get("completed_at"),
        signers=[
            Signer(
                employee_id=str(s.get("employee_id") or ""),
                role=str(s.get("role") or "signer"),
                signed_at=s.get("signed_at"),
                signature_filename=s.get("signature_filename"),
                declined_at=s.get("declined_at"),
                decline_reason=s.get("decline_reason"),
            )
            for s in (row.get("signers") or [])
            if isinstance(s, dict)
        ],
    )
