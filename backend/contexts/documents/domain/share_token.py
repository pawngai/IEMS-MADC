"""Documents domain — share-link token format.

A share token is a URL-safe base64 of ``payload + "." + signature`` where:

* ``payload`` is a base64 of a small JSON ``{"d": document_id, "f": filename,
  "exp": iso8601_expiry, "s": scope, "n": nonce}``
* ``signature`` is the HMAC-SHA256 of ``payload`` keyed by ``JWT_SECRET``

Validation is constant-time. Scope is "inline" only — never "download" —
because share links bypass the per-user RBAC gate; we deliberately prevent
mass exfiltration of locked documents through an unauthenticated channel.
The token's ``nonce`` is also recorded on document metadata so the issuer
can revoke a specific token without rotating the signing key.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any


SHARE_SCOPE_INLINE = "inline"
_DEFAULT_TTL_SECONDS_MAX = 7 * 24 * 3600  # 7 days


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def _sign(secret: str, payload_b64: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64encode(digest)


def issue_token(
    *,
    secret: str,
    document_id: str,
    filename: str,
    expires_at: datetime,
    scope: str = SHARE_SCOPE_INLINE,
) -> tuple[str, str]:
    """Returns ``(token, nonce)``. Store ``nonce`` on the document metadata
    in the ``share_token_nonces`` list so the matching share can be revoked
    later without breaking other live shares for the same document."""
    if scope != SHARE_SCOPE_INLINE:
        raise ValueError("Only 'inline' share scope is supported")
    if not secret:
        raise ValueError("Signing secret must be provided")
    nonce = secrets.token_urlsafe(16)
    payload = {
        "d": document_id,
        "f": filename,
        "exp": expires_at.astimezone(timezone.utc).isoformat(),
        "s": scope,
        "n": nonce,
    }
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(secret, payload_b64)
    return f"{payload_b64}.{signature}", nonce


def parse_token(*, secret: str, token: str) -> dict[str, Any]:
    """Verify the signature, decode the payload, raise ``ValueError`` if
    anything is off. Caller must additionally check ``exp`` against current
    time and ``nonce`` against the document's revocation list."""
    if not token or "." not in token:
        raise ValueError("Malformed share token")
    payload_b64, _, signature = token.rpartition(".")
    expected_sig = _sign(secret, payload_b64)
    if not hmac.compare_digest(expected_sig, signature):
        raise ValueError("Invalid share token signature")
    try:
        payload = json.loads(_b64decode(payload_b64).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Malformed share token payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("Malformed share token payload")
    return payload


def is_expired(payload: dict[str, Any], *, now: datetime | None = None) -> bool:
    exp = payload.get("exp")
    if not exp:
        return True
    try:
        when = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
    except ValueError:
        return True
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (now or datetime.now(timezone.utc)) >= when


def clamp_ttl_seconds(ttl_seconds: int) -> int:
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    return min(int(ttl_seconds), _DEFAULT_TTL_SECONDS_MAX)
