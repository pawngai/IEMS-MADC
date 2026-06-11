from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any

from app_platform.db.atomic import call_with_optional_session
from app_platform.domain_separation.data_ownership import assert_collection_ownership
from contexts.leave_attendance.contracts.dto import LeaveActionDTO, LeaveApplicationCreateDTO
from contexts.leave_attendance.contracts.ports import LeaveGateway
from contexts.leave_attendance.domain.leave_accounting import (
    build_account_update,
    build_debit_transaction,
    new_empty_account,
    opening_balance_for,
)
from contexts.leave_attendance.domain.leave_rules import (
    DEFAULT_LEAVE_TYPES,
    EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT,
    calculate_days,
    compute_leave_balances,
    compute_used_days_from_records,
    compute_used_days_total,
    get_leave_policy_defaults,
    get_required_supporting_document_message,
    normalize_employment_type_code,
    normalize_leave_type_record,
)
from contexts.documents.contracts.document_metadata import (
    get_accessible_document_metadata as _get_accessible_document_metadata,
)
from contexts.leave_attendance.infrastructure.document_lock import (
    lock_documents_for_finalized_leave as _lock_documents_for_finalized_leave,
)
from contexts.leave_attendance.repository.leave_repository import LeaveRuntimeRepository
from contexts.identity_access.contracts.operational import require_leave_listing_permission
from fastapi import HTTPException
from contexts.identity_access.contracts.access_control import has_authority, require_permissions
from contexts.identity_access.contracts.authorization_service import (
    EMPLOYEE,
    canPerformAction,
    resolveScopeAccess,
)
from contexts.identity_access.contracts.user_directory import get_user_department_code, get_user_display_name
from contexts.employee_master.contracts.identity_directory import (
    get_employee_department_code,
    get_employee_ids_for_department,
    get_employee_name_map,
)
from contexts.service_book.contracts.servicebook.revisions import append_revision


logger = logging.getLogger(__name__)


LEAVE_LEDGER_COLLECTION = "leave_ledger_entries"
from contexts.leave_attendance.infrastructure.gateway_helpers import (
    _build_leave_application_context as _build_leave_application_context_impl,
    _build_initial_leave_account,
    _ensure_initial_leave_account,
    _fetch_leave_balances,
    _find_employee_profile,
    _get_leave_type,
    _lock_leave_attachments_if_finalized as _lock_leave_attachments_if_finalized_impl,
    _normalize_bool,
    _normalize_leave_attachments as _normalize_leave_attachments_impl,
    _record_leave_debit as _record_leave_debit_impl,
    _resolve_service_start_date,
    _resolve_user_department,
)


async def _build_leave_application_context(*args, **kwargs):
    return await _build_leave_application_context_impl(*args, **kwargs)


async def _normalize_leave_attachments(*args, **kwargs):
    return await _normalize_leave_attachments_impl(
        *args,
        metadata_loader=_get_accessible_document_metadata,
        **kwargs,
    )


async def _record_leave_debit(*args, **kwargs):
    return await _record_leave_debit_impl(
        *args,
        append_revision_func=append_revision,
        find_employee_profile_func=_find_employee_profile,
        fetch_leave_balances_func=_fetch_leave_balances,
        **kwargs,
    )


async def _lock_leave_attachments_if_finalized(*args, **kwargs):
    return await _lock_leave_attachments_if_finalized_impl(
        *args,
        document_lock_func=_lock_documents_for_finalized_leave,
        **kwargs,
    )


class LeaveMongoGateway(LeaveGateway):
    def __init__(self, db) -> None:
        assert_collection_ownership(
            context="leave_attendance",
            collection_name="leave_applications",
            write=True,
        )
        assert_collection_ownership(
            context="leave_attendance",
            collection_name="leave_ledger_entries",
            write=True,
        )
        self._db = db
        self._repository = LeaveRuntimeRepository(db=db)

    async def get_leave_application_policy_context(
        self, payload: LeaveApplicationCreateDTO, *, current_user: dict
    ) -> dict:
        context = await _build_leave_application_context(
            self._repository,
            payload,
            current_user=current_user,
        )
        profile = context.get("profile") or {}
        balance_info = context.get("balance_info") or {}
        leave_type = context.get("leave_type") or {}

        return {
            "employee_id": context.get("employee_id") or "",
            "employee_status": profile.get("employee_status") or current_user.get("employee_status") or "ACTIVE",
            "leave_type_code": payload.leave_type_code,
            "leave_days": float(context.get("days_applied") or 0.0),
            "available_balance": balance_info.get("available_days"),
            "min_days_per_spell": leave_type.get("min_days_per_spell"),
            "max_days_per_spell": leave_type.get("max_days_per_spell"),
            "employee_gender": profile.get("gender"),
            "marital_status": profile.get("marital_status"),
            "probation_period_months": profile.get("probation_period_months"),
            "surviving_children_count": profile.get("surviving_children_count"),
            "is_single_mother": profile.get("is_single_mother"),
            "leave_from_date": payload.from_date,
            "leave_to_date": payload.to_date,
            "medical_certificate_provided": _normalize_bool(payload.medical_certificate_provided),
            "commuted_leave_basis": payload.commuted_leave_basis,
            "expected_delivery_date": payload.expected_delivery_date,
            "childbirth_date": payload.childbirth_date,
            "adoption_date": payload.adoption_date,
            "child_date_of_birth": payload.child_date_of_birth,
            "child_has_disability": _normalize_bool(payload.child_has_disability),
            "child_order": payload.child_order,
        }

    async def get_leave_balances(self, employee_id: str, *, current_user: dict) -> dict:
        profile = await _find_employee_profile(self._repository, employee_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Employee profile not found")

        profile_dept = (profile.get("current_department_id") or "").strip().upper() or None
        can_read_own = canPerformAction(
            current_user,
            required_permissions=["LEAVE_READ_OWN"],
            self_scope_only=True,
            target_employee_id=employee_id,
        )
        can_read_scoped = canPerformAction(
            current_user,
            required_permissions=["LEAVE_READ_ALL"],
            target_employee_id=employee_id,
            target_department_code=profile_dept,
        )
        if not (can_read_own or can_read_scoped):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permission to view this employee's leave balances",
            )

        emp_type = normalize_employment_type_code(
            profile.get("employment_type") or profile.get("employment_type_code")
        )
        if not emp_type:
            raise HTTPException(status_code=400, detail="Invalid employment type")
        if emp_type not in EMPLOYMENT_TYPES_WITH_LEAVE_ACCOUNT:
            raise HTTPException(
                status_code=403,
                detail="Leave account not applicable for employment type",
            )

        service_start = await _resolve_service_start_date(
            self._repository,
            employee_id=employee_id,
            profile=profile,
        )

        await _ensure_initial_leave_account(
            self._repository,
            employee_id=employee_id,
            user_id=current_user.get("sub"),
            employment_type_code=emp_type,
            service_start_date=service_start,
        )

        balances = await _fetch_leave_balances(
            self._repository, employee_id, emp_type, service_start_date=service_start
        )
        return {"employee_id": employee_id, "balances": balances}

    async def apply_leave(
        self, payload: LeaveApplicationCreateDTO, *, current_user: dict, session=None
    ) -> dict:
        context = await _build_leave_application_context(
            self._repository,
            payload,
            current_user=current_user,
        )
        employee_id = context.get("employee_id")
        days_applied = context.get("days_applied")
        balance_info = context.get("balance_info") or {}

        supporting_document_message = get_required_supporting_document_message(
            payload.leave_type_code,
            medical_certificate_provided=_normalize_bool(payload.medical_certificate_provided),
            commuted_leave_basis=payload.commuted_leave_basis,
            childbirth_date=payload.childbirth_date,
            adoption_date=payload.adoption_date,
            child_date_of_birth=payload.child_date_of_birth,
        )
        if supporting_document_message and not (payload.attachments or []):
            raise HTTPException(status_code=422, detail=supporting_document_message)

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "leave_type_code": payload.leave_type_code,
            "from_date": payload.from_date,
            "to_date": payload.to_date,
            "days_applied": days_applied,
            "reason": payload.reason,
            "leave_station": payload.leave_station,
            "contact_during_leave": payload.contact_during_leave,
            "medical_certificate_provided": _normalize_bool(payload.medical_certificate_provided),
            "commuted_leave_basis": payload.commuted_leave_basis,
            "expected_delivery_date": payload.expected_delivery_date,
            "childbirth_date": payload.childbirth_date,
            "adoption_date": payload.adoption_date,
            "child_date_of_birth": payload.child_date_of_birth,
            "child_has_disability": _normalize_bool(payload.child_has_disability),
            "child_order": payload.child_order,
            "attachments": await _normalize_leave_attachments(
                payload.attachments,
                current_user=current_user,
                db=self._db,
            ),
            "eligibility_context_version": 1,
            "eligibility_review_required": False,
            "eligibility_review_reasons": [],
            "status": "SUBMITTED",
            "applied_by": current_user.get("sub"),
            "applied_at": now,
            "balance_snapshot": balance_info,
        }

        await call_with_optional_session(
            self._repository.insert_leave_application,
            record,
            session=session,
        )
        return record

    async def list_my_leaves(self, *, current_user: dict) -> list[dict]:
        require_permissions(current_user, "LEAVE_READ_OWN")
        employee_id = current_user.get("employee_id")
        if not employee_id:
            return []
        return await self._repository.list_leave_applications(
            {"employee_id": employee_id},
            limit=200,
            sort_field="applied_at",
            sort_dir=-1,
        )

    async def list_leaves(
        self,
        *,
        status: str | None,
        leave_type_code: str | None,
        employee_id: str | None,
        current_user: dict,
    ) -> list[dict]:
        require_leave_listing_permission(current_user)

        query: dict[str, Any] = {}
        scope_access = resolveScopeAccess(current_user)
        if scope_access.get("scope") == "DEPARTMENT":
            user_dept = await _resolve_user_department(self._db, current_user)
            if not user_dept:
                raise HTTPException(
                    status_code=403,
                    detail="Department access is restricted. Map this user to a department first.",
                )

            if employee_id:
                profile = await _find_employee_profile(self._repository, employee_id)
                if not profile:
                    raise HTTPException(
                        status_code=404, detail="Employee profile not found"
                    )
                profile_dept = (
                    (profile.get("current_department_id") or "").strip().upper()
                )
                if profile_dept != user_dept:
                    raise HTTPException(
                        status_code=403,
                        detail="Department-scoped access only allows leave records from your own department",
                    )
            else:
                dept_employee_ids = await get_employee_ids_for_department(
                    self._db,
                    department_code=user_dept,
                    limit=5000,
                )
                if not dept_employee_ids:
                    return []
                query["employee_id"] = {"$in": dept_employee_ids}

        if status:
            query["status"] = status
        if leave_type_code:
            query["leave_type_code"] = leave_type_code
        if employee_id:
            query["employee_id"] = employee_id

        records = await self._repository.list_leave_applications(
            query,
            limit=500,
            sort_field="applied_at",
            sort_dir=-1,
        )

        # Enrich with employee names for recommending/sanctioning authorities
        emp_ids = list({r.get("employee_id") for r in records if r.get("employee_id")})
        if emp_ids:
            name_map = await get_employee_name_map(self._db, employee_ids=emp_ids)
            for record in records:
                record["employee_name"] = name_map.get(
                    record.get("employee_id"), record.get("employee_id")
                )

        # Resolve recommender display names for sanctioning authority context
        recommender_ids = list({r.get("recommended_by") for r in records if r.get("recommended_by")})
        if recommender_ids:
            recommender_map: dict[str, str] = {}
            for uid in recommender_ids:
                recommender_map[uid] = await get_user_display_name(self._db, user_id=uid)
            for record in records:
                rec_by = record.get("recommended_by")
                if rec_by and rec_by in recommender_map:
                    record["recommended_by_name"] = recommender_map[rec_by]

        return records

    async def recommend_leave(
        self, leave_id: str, action: LeaveActionDTO, *, current_user: dict, session=None
    ) -> dict:
        require_permissions(current_user, "LEAVE_RECOMMEND")
        record = await self._repository.find_leave_application(leave_id)
        if not record:
            raise HTTPException(status_code=404, detail="Leave application not found")
        if record.get("status") != "SUBMITTED":
            raise HTTPException(
                status_code=400, detail="Only SUBMITTED leaves can be recommended"
            )
        if record.get("applied_by") == current_user.get("sub"):
            raise HTTPException(
                status_code=403, detail="Cannot recommend your own leave"
            )

        if has_authority(current_user, "HOD"):
            applicant_profile = await _find_employee_profile(
                self._repository, record.get("employee_id")
            )
            if not applicant_profile:
                raise HTTPException(
                    status_code=404, detail="Employee profile not found"
                )
            applicant_dept = (
                (applicant_profile.get("current_department_id") or "").strip().upper()
            )
            hod_dept = await _resolve_user_department(self._db, current_user)
            if not hod_dept or applicant_dept != hod_dept:
                raise HTTPException(
                    status_code=403,
                    detail="HOD can only recommend leaves from employees in their own department",
                )

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "status": "RECOMMENDED",
            "recommended_by": current_user.get("sub"),
            "recommended_at": now,
            "remarks": action.remarks,
        }
        await call_with_optional_session(
            self._repository.update_leave_application,
            leave_id,
            update,
            session=session,
        )
        record.update(update)
        return record

    async def sanction_leave(
        self, leave_id: str, action: LeaveActionDTO, *, current_user: dict, session=None
    ) -> dict:
        record = await self._repository.find_leave_application(leave_id)
        if not record:
            raise HTTPException(status_code=404, detail="Leave application not found")

        status = record.get("status")
        leave_type = record.get("leave_type_code", "")

        # CL can be sanctioned directly by HOD (LEAVE_RECOMMEND) from SUBMITTED
        is_cl_direct = leave_type == "CL" and status == "SUBMITTED"
        if is_cl_direct:
            require_permissions(current_user, "LEAVE_RECOMMEND")
        else:
            require_permissions(current_user, "LEAVE_SANCTION")

        if status not in ("RECOMMENDED", "SUBMITTED") or (
            status == "SUBMITTED" and not is_cl_direct
        ):
            raise HTTPException(
                status_code=400,
                detail="Leave must be RECOMMENDED before it can be sanctioned",
            )
        if record.get("applied_by") == current_user.get("sub"):
            raise HTTPException(
                status_code=403, detail="Cannot sanction your own leave"
            )

        # HOD direct-sanctioning CL: validate department match
        if is_cl_direct and has_authority(current_user, "HOD"):
            applicant_profile = await _find_employee_profile(
                self._repository, record.get("employee_id")
            )
            if not applicant_profile:
                raise HTTPException(
                    status_code=404, detail="Employee profile not found"
                )
            applicant_dept = (
                (applicant_profile.get("current_department_id") or "").strip().upper()
            )
            hod_dept = await _resolve_user_department(self._db, current_user)
            if not hod_dept or applicant_dept != hod_dept:
                raise HTTPException(
                    status_code=403,
                    detail="HOD can only sanction casual leave for employees in their own department",
                )

        # Department-scope validation: DEPARTMENT-scoped users can only
        # sanction leaves for employees within their own department.
        scope_access = resolveScopeAccess(current_user)
        if scope_access.get("scope") == "DEPARTMENT":
            sanctioner_dept = await _resolve_user_department(self._db, current_user)
            applicant_profile = await _find_employee_profile(
                self._repository, record.get("employee_id")
            )
            applicant_dept = (
                (applicant_profile or {}).get("current_department_id") or ""
            ).strip().upper()
            if not sanctioner_dept or applicant_dept != sanctioner_dept:
                raise HTTPException(
                    status_code=403,
                    detail="Department-scoped users can only sanction leaves from employees in their own department",
                )

        profile = await _find_employee_profile(
            self._repository, record.get("employee_id")
        )
        if not profile:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        emp_type = normalize_employment_type_code(
            profile.get("employment_type") or profile.get("employment_type_code")
        )
        service_start = profile.get("date_of_initial_engagement")
        balances = await _fetch_leave_balances(
            self._repository,
            record.get("employee_id"),
            emp_type,
            service_start_date=service_start,
        )
        balance_info = balances.get(record.get("leave_type_code"), {})
        available = balance_info.get("available_days")
        records_ledger_transaction = balance_info.get(
            "records_ledger_transaction",
            get_leave_policy_defaults(record.get("leave_type_code")).get(
                "records_ledger_transaction",
                False,
            ),
        )
        if available is not None and record.get("days_applied", 0) > available:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient leave balance at sanction time. Available: {available}",
            )

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "status": "SANCTIONED",
            "sanctioned_by": current_user.get("sub"),
            "sanctioned_at": now,
            "remarks": action.remarks,
            "order_number": action.order_number,
            "order_date": action.order_date,
        }
        # When HOD directly sanctions CL from SUBMITTED, also fill recommendation fields
        if is_cl_direct:
            update["recommended_by"] = current_user.get("sub")
            update["recommended_at"] = now

        if records_ledger_transaction:
            await _record_leave_debit(
                self._repository,
                self._db,
                employee_id=record.get("employee_id"),
                leave_type_code=record.get("leave_type_code"),
                from_date=record.get("from_date"),
                to_date=record.get("to_date"),
                days=float(record.get("days_applied", 0)),
                user_id=current_user.get("sub"),
                available_days=float(available) if available is not None else None,
                order_number=action.order_number,
                order_date=action.order_date,
                remarks=action.remarks,
                session=session,
            )

        await call_with_optional_session(
            self._repository.update_leave_application,
            leave_id,
            update,
            session=session,
        )
        record.update(update)
        await _lock_leave_attachments_if_finalized(self._db, record)
        return record

    async def reject_leave(
        self, leave_id: str, action: LeaveActionDTO, *, current_user: dict, session=None
    ) -> dict:
        record = await self._repository.find_leave_application(leave_id)
        if not record:
            raise HTTPException(status_code=404, detail="Leave application not found")

        status = record.get("status")
        if status == "SUBMITTED":
            require_permissions(current_user, "LEAVE_RECOMMEND")
        elif status == "RECOMMENDED":
            require_permissions(current_user, "LEAVE_SANCTION")
        else:
            raise HTTPException(
                status_code=400,
                detail="Leave can only be rejected from SUBMITTED or RECOMMENDED status",
            )

        # Department-scope validation: DEPARTMENT-scoped users can only
        # reject leaves for employees within their own department.
        scope_access = resolveScopeAccess(current_user)
        if scope_access.get("scope") == "DEPARTMENT":
            rejector_dept = await _resolve_user_department(self._db, current_user)
            applicant_profile = await _find_employee_profile(
                self._repository, record.get("employee_id")
            )
            applicant_dept = (
                (applicant_profile or {}).get("current_department_id") or ""
            ).strip().upper()
            if not rejector_dept or applicant_dept != rejector_dept:
                raise HTTPException(
                    status_code=403,
                    detail="Department-scoped users can only reject leaves from employees in their own department",
                )

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "status": "REJECTED",
            "rejected_by": current_user.get("sub"),
            "rejected_at": now,
            "remarks": action.remarks,
        }
        await call_with_optional_session(
            self._repository.update_leave_application,
            leave_id,
            update,
            session=session,
        )
        record.update(update)
        await _lock_leave_attachments_if_finalized(self._db, record)
        return record

    async def cancel_leave(
        self, leave_id: str, action: LeaveActionDTO, *, current_user: dict, session=None
    ) -> dict:
        record = await self._repository.find_leave_application(leave_id)
        if not record:
            raise HTTPException(status_code=404, detail="Leave application not found")
        if record.get("status") not in ["SUBMITTED", "RECOMMENDED"]:
            raise HTTPException(
                status_code=400, detail="Only pending leaves can be cancelled"
            )
        if not canPerformAction(
            current_user,
            self_scope_only=True,
            target_employee_id=record.get("employee_id"),
        ):
            raise HTTPException(
                status_code=403, detail="Only the applicant can cancel this leave"
            )

        now = datetime.now(timezone.utc).isoformat()
        update = {
            "status": "CANCELLED",
            "remarks": action.remarks,
            "cancelled_at": now,
            "cancelled_by": current_user.get("sub"),
        }
        await call_with_optional_session(
            self._repository.update_leave_application,
            leave_id,
            update,
            session=session,
        )
        record.update(update)
        return record
