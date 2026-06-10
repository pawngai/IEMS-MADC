from __future__ import annotations

from typing import Any

from contexts.employee_master.contracts.identity_directory import resolve_identity_ref
from contexts.identity_access.contracts.access_control import require_owner_or_permissions
from contexts.identity_access.contracts.models import Permission
from contexts.service_book.application.errors import not_found
from contexts.service_book.application.service import (
    generateServiceBookPrintModel,
    validateServiceBookEligibility,
)
from contexts.service_book.contracts.service_summary_directory import get_employee_service_summary
from shared_kernel.events import utc_now_iso


class ServiceBookPrintUseCases:
    def __init__(self, *, db) -> None:
        self._db = db

    async def build_part(self, *, employee_ref: str, part_key: str, current_user: dict[str, Any]) -> dict:
        resolved_id, identity = await self._resolve(employee_ref)
        self._require_print_access(current_user, resolved_id)
        subject = await self._eligibility_subject(employee_id=resolved_id, identity=identity)
        validateServiceBookEligibility(subject)
        result = await generateServiceBookPrintModel(
            db=self._db,
            employee_id=resolved_id,
            employee_or_type=subject,
            part_key=part_key,
        )
        result["generated_at"] = utc_now_iso()
        return result

    async def build_full(self, *, employee_ref: str, current_user: dict[str, Any]) -> dict:
        resolved_id, identity = await self._resolve(employee_ref)
        self._require_print_access(current_user, resolved_id)
        subject = await self._eligibility_subject(employee_id=resolved_id, identity=identity)
        validateServiceBookEligibility(subject)
        result = await generateServiceBookPrintModel(
            db=self._db,
            employee_id=resolved_id,
            employee_or_type=subject,
        )
        result["generated_at"] = utc_now_iso()
        return result

    async def _resolve(self, ref: str) -> tuple[str, dict[str, Any]]:
        identity = await resolve_identity_ref(self._db, ref=ref)
        if not identity:
            raise not_found("Employee not found")
        return identity["employee_id"], identity

    async def _eligibility_subject(self, *, employee_id: str, identity: dict[str, Any]) -> dict[str, Any]:
        return await get_employee_service_summary(self._db, employee_id=employee_id) or identity

    @staticmethod
    def _require_print_access(current_user: dict[str, Any], employee_id: str) -> None:
        require_owner_or_permissions(
            current_user,
            employee_id,
            Permission.SERVICE_BOOK_PRINT,
            Permission.SERVICE_BOOK_READ_ALL,
        )
