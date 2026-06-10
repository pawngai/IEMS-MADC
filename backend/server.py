"""
Compatibility entrypoint.

Historically this project defined the entire FastAPI application in this file.
After the modular-monolith refactor, the canonical app lives in `backend/app/main.py`.
"""

from __future__ import annotations

import os

from app.main import app, create_app  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port)

