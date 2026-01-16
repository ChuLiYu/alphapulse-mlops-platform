"""
MLOps Pipeline schemas for system observability.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PipelineStage(BaseModel):
    """Status of a specific pipeline stage (Ingestion, Training, Serving)."""

    name: str
    status: str  # e.g., "idle", "active", "healthy", "error"
    last_run: Optional[datetime] = None
    progress: Optional[int] = Field(
        None, ge=0, le=100, description="Progress percentage if active"
    )
    latency_ms: Optional[int] = None


class DataDrift(BaseModel):
    """Data drift metrics."""

    score: float
    status: str  # "safe", "warning", "critical"
    threshold: float


class PipelineStatusResponse(BaseModel):
    """Overall pipeline health and status response."""

    overall_status: str
    stages: List[PipelineStage]
    data_drift: DataDrift


class ModelRegistryEntry(BaseModel):
    """Entry in the model registry."""

    version: str
    stage: str  # e.g., "Production", "Staging", "Archived"
    accuracy: str
    deployed: str
    status: str  # e.g., "Active", "Testing", "Inactive"


class ModelRegistryResponse(BaseModel):
    """Response containing a list of registered models."""

    models: List[ModelRegistryEntry]
