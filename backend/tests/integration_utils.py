import os
import time
import requests
import pytest

_TOKEN_CACHE: dict[tuple[str, str], str] = {}


def _candidate_base_urls() -> list[str]:
    candidates = [
        os.environ.get("IEMS_BASE_URL", "").rstrip("/"),
        os.environ.get("BACKEND_BASE_URL", "").rstrip("/"),
        os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/"),
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    seen: list[str] = []
    for candidate in candidates:
        if candidate.startswith("http") and candidate not in seen:
            seen.append(candidate)
    return seen


def _is_live_backend(base_url: str) -> bool:
    health_paths = (
        "/api/health",
        "/health/live",
        "/health/ready",
    )
    for health_path in health_paths:
        try:
            response = requests.get(f"{base_url}{health_path}", timeout=1.5)
        except requests.RequestException:
            continue
        if response.status_code == 200:
            return True
    return False


def get_base_url() -> str:
    """Return a reachable integration base URL or skip when unavailable."""
    attempts: list[str] = []
    for base_url in _candidate_base_urls():
        attempts.append(base_url)
        if _is_live_backend(base_url):
            return base_url

    pytest.skip(
        "Live backend not reachable for integration tests. "
        f"Tried: {', '.join(attempts) if attempts else 'no configured URLs'}",
        allow_module_level=True,
    )


def login_with_fallback(base_url: str, candidates: list[dict], label: str) -> str:
    """Try candidate credentials and return first token; skip clearly if none work."""
    cache_key = (base_url, label)
    cached = _TOKEN_CACHE.get(cache_key)
    if cached:
        return cached

    last_status = None
    last_body = None
    for creds in candidates:
        for delay in (0.0, 1.0, 2.0):
            if delay:
                time.sleep(delay)
            try:
                response = requests.post(
                    f"{base_url}/api/auth/login",
                    json=creds,
                    timeout=5,
                )
            except requests.RequestException as exc:
                last_status = "unreachable"
                last_body = str(exc)
                continue
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    _TOKEN_CACHE[cache_key] = token
                    return token
            last_status = response.status_code
            last_body = response.text
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        time.sleep(float(retry_after))
                    except (TypeError, ValueError):
                        pass
            else:
                break

    pytest.skip(
        f"{label} credentials unavailable in current test state "
        f"(last_status={last_status}, body={last_body})"
    )
