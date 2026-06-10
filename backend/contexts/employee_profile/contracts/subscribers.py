"""Public contract for employee read-model subscriber registration.

Bootstrap/middleware code should import from here, NOT from
``contexts.employee_profile.read_model.application.subscribers`` directly.
"""

from __future__ import annotations

from contexts.employee_profile.read_model.application.subscribers import (  # noqa: F401
    register_employee_read_model_subscribers,
)

__all__ = ["register_employee_read_model_subscribers"]
