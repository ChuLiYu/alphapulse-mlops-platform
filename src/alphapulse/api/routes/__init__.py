"""
API routes for AlphaPulse FastAPI application.

This module exports all route routers for inclusion in the main FastAPI app.
"""

from .health import router as health_router
from .prices import router as prices_router
from .signals import router as signals_router

__all__ = [
    "health_router",
    "prices_router",
    "signals_router",
]
