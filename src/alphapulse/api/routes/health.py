"""
Health check endpoints for API monitoring and load balancer integration.

These endpoints are critical for production deployment and
infrastructure monitoring (AWS ELB/ALB, Kubernetes liveness probes).
"""

import time
import psutil
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from alphapulse.api.database import get_db
from alphapulse.api.schemas.health import HealthDetailed, HealthStatus

router = APIRouter()

# Store application start time for uptime calculation
APP_START_TIME = time.time()


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
    components: Dict[str, str] = {
        "api": "healthy",
        "database": "unhealthy",
    }

    try:
        db.execute(text("SELECT 1"))
        components["database"] = "healthy"
        database_message = "Database connection successful"
    except Exception as e:
        database_message = f"Database error: {str(e)}"

    overall_status = (
        "healthy"
        if all(status == "healthy" for status in components.values())
        else "unhealthy"
    )

    uptime_seconds = time.time() - APP_START_TIME

    return HealthDetailed(
        overall=overall_status,
        components=components,
        timestamp=datetime.utcnow(),
        uptime=uptime_seconds,
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
    process = psutil.Process()

    uptime_seconds = time.time() - APP_START_TIME
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / (1024 * 1024)
    cpu_percent = process.cpu_percent(interval=0.1)

    try:
        connections = len(process.connections())
    except (psutil.AccessDenied, OSError):
        connections = 0

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "uptime": round(uptime_seconds, 2),
            "memory_usage_mb": round(memory_mb, 2),
            "memory_usage_percent": round(process.memory_percent(), 2),
            "cpu_usage_percent": round(cpu_percent, 2),
            "active_connections": connections,
        },
    }
