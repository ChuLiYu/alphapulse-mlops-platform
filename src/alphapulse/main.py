"""
AlphaPulse FastAPI Application Entry Point

This module initializes the FastAPI application with proper Decimal support
for financial data processing.
"""

import os
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic.json import pydantic_encoder


# Custom JSON encoder for Decimal types
def decimal_encoder(obj: Any) -> Any:
    """Custom JSON encoder that converts Decimal to string."""
    if isinstance(obj, Decimal):
        return str(obj)
    return pydantic_encoder(obj)


# Get root path from environment (for reverse proxy)
root_path = os.getenv("ROOT_PATH", "")

# Create FastAPI application
app = FastAPI(
    title="AlphaPulse Trading API",
    description="Backend infrastructure for cryptocurrency trading signal systems",
    version="1.0.0",
    root_path=root_path,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Ensure static monitoring directory exists
os.makedirs("static/monitoring", exist_ok=True)

# Mount static files for Evidently AI reports
app.mount(
    "/api/monitoring",
    StaticFiles(directory="static/monitoring", html=True),
    name="monitoring",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Override default JSON encoder to handle Decimal
app.json_encoder = decimal_encoder


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AlphaPulse Trading API",
        "version": "1.0.0",
        "description": "Backend infrastructure for cryptocurrency trading signal systems",
        "docs": "/api/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer integration."""
    return {
        "status": "healthy",
        "service": "AlphaPulse API",
        "timestamp": "2026-01-10T21:55:00Z",
    }


# Import routers after app creation to avoid circular imports
from alphapulse.api.routes import (
    auth,
    health,
    indicators,
    prices,
    signals,
    simulation,
    ops,
    security,
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(prices.router, prefix="/api/v1", tags=["prices"])
app.include_router(signals.router, prefix="/api/v1", tags=["signals"])
app.include_router(indicators.router, prefix="/api/v1", tags=["indicators"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(simulation.router, prefix="/api/v1", tags=["simulation"])
app.include_router(ops.router, prefix="/api/v1", tags=["mlops"])
# app.include_router(security.router, prefix="/api/v1", tags=["security"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
