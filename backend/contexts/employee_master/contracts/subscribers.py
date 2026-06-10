"""Employee Master read-model subscriber registration contract.

Bootstrap/middleware should import subscriber registration from here. Adapts the
existing employee_profile read-model subscriber while Employee Master becomes the
canonical boundary.
"""

from contexts.employee_profile.contracts.subscribers import (  # noqa: F401
    register_employee_read_model_subscribers,
)

__all__ = ["register_employee_read_model_subscribers"]
