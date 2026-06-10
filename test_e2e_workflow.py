"""Current live workflow mutation entrypoint.

The historical script in this file targeted the retired `/api/profile/v2` write
surface. The canonical live workflow coverage now lives in
`backend/tests/test_rbac_workflow.py` and exercises the split
EmployeeIdentity/EmployeeProfile API:

- create employee identity and profile enrichment
- submit, verify, activate identity
- submit, verify, approve, lock profile
- reject invalid transitions and locked-record writes
- verify audit trail availability
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

base_with_api = os.getenv("IEMS_E2E_BASE", "").rstrip("/")
if base_with_api.endswith("/api") and not os.getenv("IEMS_BASE_URL"):
    os.environ["IEMS_BASE_URL"] = base_with_api[:-4]


if __name__ == "__main__":
    print(
        "Delegating to backend/tests/test_rbac_workflow.py; "
        "legacy /api/profile/v2 side-effect seeding is retired."
    )
    raise SystemExit(pytest.main(["backend/tests/test_rbac_workflow.py", "-q"]))
