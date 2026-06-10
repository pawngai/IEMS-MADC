from __future__ import annotations

from contextlib import contextmanager


@contextmanager
def span(name: str):
    _ = name
    yield
