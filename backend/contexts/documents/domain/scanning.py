"""Documents domain — malware scanning contract.

A scanner inspects upload bytes and returns a ``ScanResult``. Status values
are persisted on metadata as ``scan_status`` and gate read access:

* ``CLEAN``      — file passed scanning and is safe to serve
* ``PENDING``    — scan hasn't run or is still running (async scanners)
* ``INFECTED``   — threat detected; file is quarantined and never served
* ``ERROR``      — scan failed; serving is gated by
                   ``DOCUMENT_SCANNER_BLOCK_ON_PENDING``
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ScanStatus:
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    ERROR = "ERROR"

    ALL = frozenset({PENDING, CLEAN, INFECTED, ERROR})


@dataclass(frozen=True, slots=True)
class ScanResult:
    status: str
    backend: str
    threat_name: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ScanStatus.ALL:
            raise ValueError(f"Invalid scan status: {self.status!r}")


class MalwareScanner(Protocol):
    backend_name: str

    def scan(self, contents: bytes, *, content_type: str | None = None) -> ScanResult:
        ...
