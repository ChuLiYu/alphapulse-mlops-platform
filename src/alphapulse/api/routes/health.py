"""
Health check endpoints for API monitoring and load balancer integration.

These endpoints are critical for production deployment and
infrastructure monitoring (AWS ELB/ALB, Kubernetes liveness probes).
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.alphapulse.api.database import get_db
from src.alphapulse.api.schemas.health import HealthDetailed, HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Basic health check endpoint for load balancer integration.

    This endpoint should:
    1. Return 200 OK if service is healthy
    2. Be lightweight (no database queries)
    3. Used by AWS ELB/ALB for health checks

    Returns:
        HealthStatus: Basic health information
    """
    return HealthStatus(
        status="healthy",
        service="AlphaPulse API",
        timestamp=datetime.utcnow(),
        message="Service is operational",
    )


@router.get("/health/detailed", response_model=HealthDetailed)
async def health_detailed(db: Session = Depends(get_db)):
    """
    Detailed health check with component status.

    This endpoint checks:
    1. Database connectivity
    2. Other external dependencies (if any)
    3. Service health metrics

    Args:
        db: Database session dependency

    Returns:
        HealthDetailed: Detailed health status with component checks
    """
    components: Dict[str, str] = {
        "api": "healthy",
        "database": "unhealthy",  # Default to unhealthy until verified
    }

    # Check database connectivity
    try:
        db.execute("SELECT 1")
        components["database"] = "healthy"
        database_message = "Database connection successful"
    except Exception as e:
        database_message = f"Database error: {str(e)}"

    # Determine overall status
    overall_status = (
        "healthy"
        if all(status == "healthy" for status in components.values())
        else "unhealthy"
    )

    return HealthDetailed(
        overall=overall_status,
        components=components,
        timestamp=datetime.utcnow(),
        message=f"Database: {database_message}",
    )


@router.get("/health/readiness")
async def readiness_probe():
    """
    Readiness probe for Kubernetes/container orchestration.

    This endpoint indicates whether the service is ready to
    receive traffic. Should check all dependencies.

    Returns:
        dict: Readiness status
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AlphaPulse API",
        "message": "Service is ready to receive traffic",
    }


@router.get("/health/liveness")
async def liveness_probe():
    """
    Liveness probe for Kubernetes/container orchestration.

    This endpoint indicates whether the service is alive.
    Should be lightweight and fast.

    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AlphaPulse API",
        "message": "Service is alive and running",
    }


@router.get("/health/metrics")
async def health_metrics():
    """
    Health metrics endpoint for monitoring systems.

    Returns basic metrics that can be consumed by
    monitoring systems like Prometheus.

    Returns:
        dict: Health metrics
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "uptime": "TODO: Implement uptime tracking",
            "memory_usage": "TODO: Implement memory tracking",
            "cpu_usage": "TODO: Implement CPU tracking",
            "active_connections": "TODO: Implement connection tracking",
        },
    }
