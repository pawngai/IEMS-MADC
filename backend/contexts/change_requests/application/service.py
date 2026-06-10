from __future__ import annotations

from datetime import datetime, timezone

from contexts.employee_identity.contracts.events import EmployeeUpdatedEvent
from app_platform.db.atomic import call_with_optional_session, run_atomic
from app_platform.event_bus.types import EventName
from app_platform.outbox.model import OutboxEvent
from app_platform.outbox.repo import OutboxRepository
from contexts.change_requests.contracts.dto import CreateChangeRequestDTO
from contexts.change_requests.contracts.ports import ChangeRequestGateway


class ChangeRequestApplicationService:
    def __init__(self, *, gateway: ChangeRequestGateway, outbox_repo: OutboxRepository | None) -> None:
        self._gateway = gateway
        self._outbox_repo = outbox_repo

    async def _enqueue_event(
        self,
        *,
        name: str,
        payload: dict,
        actor_id: str | None,
        department_id: str | None,
        session=None,
    ) -> None:
        if self._outbox_repo is None:
            return
        await call_with_optional_session(
            self._outbox_repo.add_event,
            OutboxEvent(
                name=name,
                payload=payload,
                actor_id=actor_id,
                department_id=department_id,
            ),
            session=session,
        )

    async def create_change_request(self, payload: CreateChangeRequestDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.create_change_request,
                payload,
                current_user=current_user,
                session=session,
            )
            await self._enqueue_event(
                name=EventName.CHANGE_REQUEST_SUBMITTED.value,
                payload={
                    "request_id": result.get("request_id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "request_type": result.get("request_type"),
                    "category": result.get("category"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await run_atomic(getattr(self._gateway, "_db", None), _operation)

    async def list_my_change_requests(self, *, current_user: dict, status: str | None = None) -> dict:
        return await self._gateway.list_my_change_requests(current_user=current_user, status=status)

    async def get_change_request(self, request_id: str, *, current_user: dict) -> dict:
        return await self._gateway.get_change_request(request_id, current_user=current_user)

    async def cancel_change_request(self, request_id: str, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.cancel_change_request,
                request_id,
                current_user=current_user,
                session=session,
            )
            await self._enqueue_event(
                name=EventName.CHANGE_REQUEST_CANCELLED.value,
                payload={
                    "request_id": result.get("request_id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await run_atomic(getattr(self._gateway, "_db", None), _operation)

    async def list_change_requests(
        self,
        *,
        current_user: dict,
        status: str | None = None,
        employee_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        return await self._gateway.list_change_requests(
            current_user=current_user,
            status=status,
            employee_id=employee_id,
            page=page,
            page_size=page_size,
        )

    async def review_change_request(
        self,
        request_id: str,
        *,
        action: str,
        remarks: str | None,
        current_user: dict,
    ) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.review_change_request,
                request_id,
                action=action,
                remarks=remarks,
                current_user=current_user,
                session=session,
            )

            status = (result.get("status") or "").upper()
            if status == "APPLIED":
                event_name = EventName.CHANGE_REQUEST_APPLIED.value
            elif status == "REJECTED":
                event_name = EventName.CHANGE_REQUEST_REJECTED.value
            else:
                event_name = None

            if event_name:
                await self._enqueue_event(
                    name=event_name,
                    payload={
                        "request_id": result.get("request_id"),
                        "employee_id": result.get("employee_id"),
                        "status": result.get("status"),
                        "request_type": result.get("request_type"),
                        "category": result.get("category"),
                    },
                    actor_id=current_user.get("sub"),
                    department_id=current_user.get("department_code"),
                    session=session,
                )

            if status == "APPLIED" and str(result.get("request_type") or "").upper() == "PROFILE":
                fields = result.get("fields") or []
                patch = {
                    field.get("field_name"): field.get("requested_value")
                    for field in fields
                    if isinstance(field, dict) and field.get("field_name")
                }
                employee_id = result.get("employee_id")
                if employee_id and patch:
                    event = EmployeeUpdatedEvent(
                        employee_id=employee_id,
                        patch=patch,
                        updated_at=result.get("updated_at")
                        or datetime.now(timezone.utc).isoformat(),
                        version=1,
                    )
                    await self._enqueue_event(
                        name=EventName.EMPLOYEE_UPDATED.value,
                        payload=event.model_dump(mode="json"),
                        actor_id=current_user.get("sub"),
                        department_id=current_user.get("department_code"),
                        session=session,
                    )
            return result

        return await run_atomic(getattr(self._gateway, "_db", None), _operation)

    async def get_pending_count(self, *, current_user: dict) -> int:
        return await self._gateway.get_pending_count(current_user=current_user)
