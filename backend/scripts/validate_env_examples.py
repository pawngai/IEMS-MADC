from __future__ import annotations

import re
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _pattern_for(key: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*#?\s*{re.escape(key)}\s*=", re.MULTILINE)


def _validate_template(path: Path, required_keys: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    missing = [key for key in required_keys if not _pattern_for(key).search(text)]
    return missing


def main() -> int:
    templates = {
        ROOT / ".env.example": [
            "MONGO_URL",
            "DB_NAME",
            "JWT_SECRET",
            "ENVIRONMENT",
            "IEMS_E2E_DE_PASSWORD",
            "IEMS_E2E_VERIFIER_PASSWORD",
            "IEMS_E2E_ESTABLISHMENT_PASSWORD",
            "IEMS_E2E_HOO_PASSWORD",
            "IEMS_E2E_DEALING_PASSWORD",
            "IEMS_E2E_AUDITOR_PASSWORD",
            "CORS_ORIGINS",
            "CORS_ORIGIN_REGEX",
            "RATE_LIMIT_STORAGE_URI",
            "API_TITLE",
            "API_DESCRIPTION",
            "API_VERSION",
            "UPLOAD_DIR",
            "REACT_APP_BACKEND_URL",
        ],
        ROOT / "backend" / ".env.example": [
            "MONGO_URL",
            "DB_NAME",
            "JWT_SECRET",
            "ENVIRONMENT",
            "IEMS_E2E_DE_PASSWORD",
            "IEMS_E2E_VERIFIER_PASSWORD",
            "IEMS_E2E_ESTABLISHMENT_PASSWORD",
            "IEMS_E2E_HOO_PASSWORD",
            "IEMS_E2E_DEALING_PASSWORD",
            "IEMS_E2E_AUDITOR_PASSWORD",
            "CORS_ORIGINS",
            "CORS_ORIGIN_REGEX",
            "RATE_LIMIT_STORAGE_URI",
            "API_TITLE",
            "API_DESCRIPTION",
            "API_VERSION",
            "UPLOAD_DIR",
        ],
        ROOT / "deploy" / "gcp" / ".env.example": [
            "BACKEND_IMAGE",
            "ENVIRONMENT",
            "MONGO_URL",
            "DB_NAME",
            "JWT_SECRET",
            "CORS_ORIGINS",
            "RATE_LIMIT_STORAGE_URI",
            "UPLOAD_DIR",
            "DOCUMENT_STORAGE_BACKEND",
            "API_TITLE",
            "API_DESCRIPTION",
            "API_VERSION",
        ],
    }

    failures: list[tuple[Path, list[str]]] = []
    for path, required_keys in templates.items():
        if not path.exists():
            failures.append((path, ["<missing file>"]))
            continue

        missing = _validate_template(path, required_keys)
        if missing:
            failures.append((path, missing))

    if failures:
        print("Environment template validation failed:")
        for path, missing in failures:
            print(f"- {path.relative_to(ROOT)}")
            for key in missing:
                print(f"  - missing {key}")
        return 1

    print("Environment template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
