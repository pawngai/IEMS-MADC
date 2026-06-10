from __future__ import annotations

from app_platform.event_bus.bus import EventBus
from app_platform.event_bus.types import BaseEvent, EventName
from contexts.notifications.domain.model import NotificationMessage
from contexts.notifications.infrastructure.repo import NotificationRepository
from shared_kernel.events import utc_now_iso


def register_notification_subscribers(*, event_bus: EventBus, db_provider) -> None:
    async def _on_leave_approved(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return

        payload = event.payload or {}
        employee_id = payload.get("employee_id")
        if not employee_id:
            return

        leave_id = payload.get("leave_id") or ""
        leave_type_code = payload.get("leave_type_code") or "Leave"
        days_applied = payload.get("days_applied")

        message = NotificationMessage(
            id=f"notif-{event.event_id}",
            employee_id=employee_id,
            type="LEAVE_STATUS",
            title="Leave Application Approved",
            message=(
                f"Your {leave_type_code} leave request"
                f" ({leave_id}) has been approved"
                + (f" for {days_applied} day(s)." if days_applied is not None else ".")
            ),
            level="success",
            timestamp=utc_now_iso(),
            action_url="/ess/leave",
            source_event_id=event.event_id,
        )

        repo = NotificationRepository(db)
        await repo.add(message)

    async def _on_change_request_reviewed(event: BaseEvent) -> None:
        db = db_provider()
        if db is None:
            return

        payload = event.payload or {}
        employee_id = payload.get("employee_id")
        if not employee_id:
            return

        request_id = payload.get("request_id") or ""
        category = payload.get("category") or "Change Request"
        request_type = (payload.get("request_type") or "CHANGE").lower()

        approved = event.name == EventName.CHANGE_REQUEST_APPLIED.value
        title = "Change Request Approved & Applied" if approved else "Change Request Rejected"
        message_text = (
            f"Your {request_type} change request ({category})"
            f" [{request_id}] has been approved and applied."
            if approved
            else f"Your {request_type} change request ({category}) [{request_id}] was rejected."
        )

        message = NotificationMessage(
            id=f"notif-{event.event_id}",
            employee_id=employee_id,
            type="CHANGE_REQUEST",
            title=title,
            message=message_text,
            level="success" if approved else "warning",
            timestamp=utc_now_iso(),
            action_url="/ess/change-requests",
            source_event_id=event.event_id,
        )

        repo = NotificationRepository(db)
        await repo.add(message)

    event_bus.subscribe(EventName.LEAVE_APPROVED.value, _on_leave_approved)
    event_bus.subscribe(EventName.CHANGE_REQUEST_APPLIED.value, _on_change_request_reviewed)
    event_bus.subscribe(EventName.CHANGE_REQUEST_REJECTED.value, _on_change_request_reviewed)
