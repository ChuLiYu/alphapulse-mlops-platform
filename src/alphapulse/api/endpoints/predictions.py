"""
FastAPI endpoints for model predictions.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from alphapulse.api.model_predictor import get_predictor

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])


class PredictionResponse(BaseModel):
    """Response model for single prediction."""

    ticker: str
    current_date: str
    current_price: float
    predicted_change: float
    predicted_price: float
    predicted_direction: str
    confidence: str
    model_name: str
    timestamp: str


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions."""

    tickers: List[str] = Field(..., min_items=1, max_items=10)


class ModelInfoResponse(BaseModel):
    """Response model for model information."""

    model_loaded: bool
    model_path: str
    model_name: Optional[str] = None
    validation_mae: Optional[float] = None
    test_mae: Optional[float] = None
    test_r2: Optional[float] = None
    training_time: Optional[float] = None
    trained_at: Optional[str] = None
    total_iterations: Optional[int] = None
    overfit_count: Optional[int] = None


@router.get("/predict/{ticker}", response_model=PredictionResponse)
async def predict_single(ticker: str = "BTC-USD"):
    """
    Predict next day price change for a single ticker.

    Args:
        ticker: Asset ticker symbol (default: BTC-USD)

    Returns:
        Prediction results
    """
    try:
        predictor = get_predictor()
        result = predictor.predict_next_day(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict/batch", response_model=List[PredictionResponse])
async def predict_batch(request: BatchPredictionRequest):
    """
    Predict next day price changes for multiple tickers.

    Args:
        request: List of ticker symbols

    Returns:
        List of prediction results
    """
    try:
        predictor = get_predictor()
        results = predictor.predict_batch(request.tickers)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Get information about the currently loaded model.

    Returns:
        Model information including performance metrics
    """
    try:
        predictor = get_predictor()
        info = predictor.get_model_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/reload")
async def reload_model():
    """
    Reload the model from disk.

    Useful after retraining to load the new model without restarting the service.

    Returns:
        Success message
    """
    try:
        predictor = get_predictor()
        predictor.reload_model()
        return {"status": "success", "message": "Model reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
