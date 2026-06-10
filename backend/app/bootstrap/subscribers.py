from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_app_subscribers(app) -> None:
    container = getattr(app.state, "container", None)
    if container is None:
        return

    try:
        from contexts.audit.application.subscribers import register_audit_subscribers
        from contexts.documents.application.subscribers import register_documents_subscribers
        from contexts.employee_master.contracts.subscribers import (
            register_employee_read_model_subscribers,
        )
        from contexts.notifications.application.subscribers import (
            register_notification_subscribers,
        )
        from contexts.service_book.contracts.subscribers import (
            register_service_book_subscribers,
        )
        from contexts.service_book.records.contracts.subscribers import (
            register_service_event_subscribers,
        )

        register_audit_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
        register_documents_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
        register_notification_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
        register_employee_read_model_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
        register_service_book_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
        register_service_event_subscribers(
            event_bus=container.event_bus,
            db_provider=lambda: getattr(app.state, "db", None),
        )
    except Exception as exc:
        logger.exception("Failed to register one or more module subscribers")
        raise RuntimeError("Critical subscriber registration failed") from exc


