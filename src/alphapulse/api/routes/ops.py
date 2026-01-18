"""
MLOps Pipeline Observability endpoints.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from alphapulse.api.models_user import User
from alphapulse.api.schemas.ops import (
    DataDrift,
    ModelRegistryEntry,
    ModelRegistryResponse,
    PipelineStage,
    PipelineStatusResponse,
)
from alphapulse.security.auth import get_current_user_from_token

router = APIRouter(prefix="/ops", tags=["mlops"])

import random


@router.get("/pipeline-status", response_model=PipelineStatusResponse)
async def get_pipeline_status():
    """
    Get the current health status of the MLOps pipeline.
    """
    now = datetime.utcnow()

    # Add some dynamic variety for demo purposes
    progress = random.randint(40, 85)
    latency = random.randint(105, 135)
    # Drift score slightly higher to show model is being monitored for potential decay
    drift_score = round(random.uniform(0.045, 0.065), 3)

    return PipelineStatusResponse(
        overall_status="healthy",
        stages=[
            PipelineStage(
                name="Ingestion", status="idle", last_run=now - timedelta(minutes=45)
            ),
            PipelineStage(name="Training", status="active", progress=progress),
            PipelineStage(name="Serving", status="healthy", latency_ms=latency),
        ],
        data_drift=DataDrift(score=drift_score, status="safe", threshold=0.1),
    )


@router.get("/models", response_model=ModelRegistryResponse)
async def get_model_registry():
    """
    Get the list of registered models and their deployment status.
    """
    return ModelRegistryResponse(
        models=[
            ModelRegistryEntry(
                version="v2.4.1",
                stage="Production",
                accuracy="58.2%",
                deployed="2 days ago",
                status="Active",
            ),
            ModelRegistryEntry(
                version="v2.5.0-rc1",
                stage="Staging",
                accuracy="61.5%",
                deployed="5 hours ago",
                status="Testing",
            ),
            ModelRegistryEntry(
                version="v2.4.0",
                stage="Archived",
                accuracy="57.8%",
                deployed="14 days ago",
                status="Inactive",
            ),
        ]
    )


@router.get("/drift-analysis")
async def get_drift_analysis():
    """
    Get detailed data drift analysis (Mock for Frontend).
    """
    return {
        "overall_status": "stable",
        "drift_score": 0.05,
        "features": [
            {"name": "price_volatility", "drift": 0.02, "status": "stable"},
            {"name": "trading_volume", "drift": 0.12, "status": "warning"},
            {"name": "market_sentiment", "drift": 0.04, "status": "stable"},
        ],
        "timestamp": datetime.utcnow(),
    }
