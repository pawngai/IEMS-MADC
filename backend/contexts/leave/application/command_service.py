from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException

from app_platform.db.atomic import call_with_optional_session, run_atomic
from app_platform.event_bus.types import EventName
from contexts.leave.application.eventing import LeaveEventPublisher
from contexts.leave.contracts.dto import LeaveActionDTO, LeaveApplicationCreateDTO
from contexts.leave.contracts.ports import LeaveGateway


class LeaveCommandService:
    def __init__(
        self,
        *,
        gateway: LeaveGateway,
        event_publisher: LeaveEventPublisher,
        leave_rules_evaluator: Callable[[dict], dict] | None = None,
    ) -> None:
        self._gateway = gateway
        self._event_publisher = event_publisher
        self._leave_rules_evaluator = leave_rules_evaluator

    async def _run_atomic(self, operation):
        db = getattr(self._gateway, "_db", None)
        return await run_atomic(db, operation)

    async def apply_leave(self, payload: LeaveApplicationCreateDTO, *, current_user: dict) -> dict:
        if self._leave_rules_evaluator is not None:
            facts = await self._gateway.get_leave_application_policy_context(
                payload,
                current_user=current_user,
            )
            decision = self._leave_rules_evaluator(facts)
            if not decision.get("allowed", True):
                raise HTTPException(
                    status_code=400,
                    detail="; ".join(decision.get("reasons") or ["Policy denied"]),
                )

        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.apply_leave,
                payload,
                current_user=current_user,
                session=session,
            )
            await self._event_publisher.publish(
                name=EventName.LEAVE_APPLIED.value,
                payload={
                    "leave_id": result.get("id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "leave_type_code": result.get("leave_type_code"),
                    "days_applied": result.get("days_applied"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await self._run_atomic(_operation)

    async def recommend_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.recommend_leave,
                leave_id,
                action,
                current_user=current_user,
                session=session,
            )
            await self._event_publisher.publish(
                name=EventName.LEAVE_RECOMMENDED.value,
                payload={
                    "leave_id": result.get("id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "leave_type_code": result.get("leave_type_code"),
                    "days_applied": result.get("days_applied"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await self._run_atomic(_operation)

    async def sanction_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.sanction_leave,
                leave_id,
                action,
                current_user=current_user,
                session=session,
            )
            await self._event_publisher.publish(
                name=EventName.LEAVE_APPROVED.value,
                payload={
                    "leave_id": result.get("id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "leave_type_code": result.get("leave_type_code"),
                    "days_applied": result.get("days_applied"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await self._run_atomic(_operation)

    async def reject_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.reject_leave,
                leave_id,
                action,
                current_user=current_user,
                session=session,
            )
            await self._event_publisher.publish(
                name=EventName.LEAVE_REJECTED.value,
                payload={
                    "leave_id": result.get("id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "leave_type_code": result.get("leave_type_code"),
                    "days_applied": result.get("days_applied"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await self._run_atomic(_operation)

    async def cancel_leave(self, leave_id: str, action: LeaveActionDTO, *, current_user: dict) -> dict:
        async def _operation(session):
            result = await call_with_optional_session(
                self._gateway.cancel_leave,
                leave_id,
                action,
                current_user=current_user,
                session=session,
            )
            await self._event_publisher.publish(
                name=EventName.LEAVE_CANCELLED.value,
                payload={
                    "leave_id": result.get("id"),
                    "employee_id": result.get("employee_id"),
                    "status": result.get("status"),
                    "leave_type_code": result.get("leave_type_code"),
                    "days_applied": result.get("days_applied"),
                },
                actor_id=current_user.get("sub"),
                department_id=current_user.get("department_code"),
                session=session,
            )
            return result

        return await self._run_atomic(_operation)
