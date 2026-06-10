"""FastAPI application package.

Submodules:

- ``app.main`` — uvicorn entry-point exposing ``app``.
- ``app.bootstrap`` — app-factory, container wiring, router registry,
  startup subscribers.
- ``app.middleware``, ``app.observability``, ``app.security`` — cross-cutting
  request middleware and observability helpers.

The slowapi limiter lives in ``app_platform.web.rate_limit`` (not here).
"""
