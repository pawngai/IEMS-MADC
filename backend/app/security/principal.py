from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Principal:
    user_id: str
    roles: list[str] = field(default_factory=list)
    department_id: str | None = None
    scopes: list[str] = field(default_factory=list)


def principal_from_user_payload(user: dict) -> Principal:
    authorities = [str(x) for x in (user.get("authorities") or [])]
    return Principal(
        user_id=user.get("sub") or "",
        roles=authorities,
        department_id=user.get("department_code") or None,
        scopes=authorities,
    )
