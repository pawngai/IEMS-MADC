from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Decision:
    allowed: bool = True
    reasons: list[str] = field(default_factory=list)
    required_approvals: list[str] = field(default_factory=list)

    def deny(self, reason: str) -> None:
        self.allowed = False
        self.reasons.append(reason)
