"""
Health check schemas for API monitoring and load balancer integration.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health status response for load balancer integration."""

    status: str = Field(
        ..., example="healthy", description="Overall health status (healthy/unhealthy)"
    )
    service: str = Field(..., example="AlphaPulse API", description="Service name")
    timestamp: datetime = Field(
        ..., example="2026-01-10T21:55:00Z", description="Timestamp of health check"
    )
    database: Optional[str] = Field(
        None, example="connected", description="Database connection status"
    )
    redis: Optional[str] = Field(
        None, example="connected", description="Redis connection status"
    )
    message: Optional[str] = Field(
        None,
        example="All systems operational",
        description="Additional health information",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "AlphaPulse API",
                "timestamp": "2026-01-10T21:55:00Z",
                "database": "connected",
                "redis": "connected",
                "message": "All systems operational",
            }
        }


class HealthDetailed(BaseModel):
    """Detailed health check response with component status."""

    overall: str = Field(..., example="healthy", description="Overall health status")
    components: dict[str, str] = Field(
        ...,
        example={
            "database": "healthy",
            "redis": "healthy",
            "api": "healthy",
            "storage": "healthy",
        },
        description="Health status of individual components",
    )
    timestamp: datetime = Field(..., description="Timestamp of health check")
    uptime: Optional[float] = Field(
        None, example=86400.5, description="Service uptime in seconds"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
