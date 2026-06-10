from __future__ import annotations

from pathlib import Path

# Path shim: MongoDB migration/backfill scripts (backend/scripts/mongodb/)
# add the project root to sys.path and import via `backend.contexts.*` or
# `backend.scripts.*`.  The __path__ extension lets those resolve to sibling
# packages inside the backend/ directory.  Production code must NOT use
# `backend.*` imports — see test_target_architecture_enforcement.py.
_pkg_dir = Path(__file__).resolve().parent
_parent_dir = _pkg_dir.parent
__path__ = [str(_pkg_dir), str(_parent_dir)]
