"""
AlphaPulse FastAPI Application Entry Point

This module initializes the FastAPI application with proper Decimal support
for financial data processing.
"""

from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic.json import pydantic_encoder


# Custom JSON encoder for Decimal types
def decimal_encoder(obj: Any) -> Any:
    """Custom JSON encoder that converts Decimal to string."""
    if isinstance(obj, Decimal):
        return str(obj)
    return pydantic_encoder(obj)


# Create FastAPI application
app = FastAPI(
    title="AlphaPulse Trading API",
    description="Backend infrastructure for cryptocurrency trading signal systems",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
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
        "docs": "/docs",
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
from src.alphapulse.api.routes import auth, health, indicators, prices, signals

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(prices.router, prefix="/api/v1", tags=["prices"])
app.include_router(signals.router, prefix="/api/v1", tags=["signals"])
app.include_router(indicators.router, prefix="/api/v1", tags=["indicators"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
