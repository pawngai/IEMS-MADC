"""Employee Master identity read contract.

This module adapts the existing employee_identity contract while Employee
Master becomes the canonical boundary for current employee facts.
"""

from contexts.employee_master.identity.contracts.identity_directory import *  # noqa: F401,F403

