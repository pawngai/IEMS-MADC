import os
import sys


def test_app_import_and_key_routes_mounted():
    # Ensure `backend/` is on sys.path so imports match runtime (`python backend/server.py`).
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from app.main import app

    paths = {getattr(r, "path", "") for r in app.routes}

    # API root + health
    assert "/api/" in paths
    assert "/api/health" in paths

    # Identity
    assert "/api/auth/login" in paths
    assert "/api/auth/me" in paths
    assert "/api/users/" in paths

    # Masters + Forms + Documents
    assert "/api/masters/employment-types" in paths
    assert "/api/forms/employee-profile" in paths
    assert "/api/documents/photo" in paths
    assert "/api/documents/files" in paths
    assert "/api/documents/files/{filename}/download" in paths
    assert "/api/documents/files/{filename}/metadata" in paths
    assert "/api/ess/my-documents" in paths
    assert "/api/ess/my-documents/{filename}" in paths
    assert "/api/ess/my-documents/{filename}/download" in paths

