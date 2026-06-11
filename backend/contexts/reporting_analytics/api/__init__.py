"""Reporting API package exports."""

from contexts.reporting_analytics.api import router
from contexts.reporting_analytics.api.router import reporting_router

__all__ = ["reporting_router", "router"]
