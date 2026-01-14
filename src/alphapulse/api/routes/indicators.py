"""
Technical indicator endpoints with Decimal precision.

These endpoints provide access to technical indicators calculated
by the data pipeline, with strict Decimal type enforcement.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from src.alphapulse.api.database import get_db
from src.alphapulse.api.models import TechnicalIndicator
from src.alphapulse.api.schemas.indicator import (
    IndicatorCreate,
    IndicatorData,
    IndicatorListResponse,
    IndicatorResponse,
    IndicatorStatsResponse,
)

router = APIRouter()


@router.get("/indicators", response_model=IndicatorListResponse)
async def get_indicators(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for time range"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for time range"),
    indicator_type: Optional[str] = Query(
        None, description="Filter by indicator type (trend, momentum, volatility)"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """
    Get technical indicator data with Decimal precision.

    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        start_date: Start of time range
        end_date: End of time range
        indicator_type: Type of indicator to filter by
        limit: Maximum records to return (1-1000)
        offset: Records to skip (for pagination)
        db: Database session

    Returns:
        IndicatorListResponse: List of technical indicator records
    """
    # Build query
    query = db.query(TechnicalIndicator)

    # Apply filters
    if symbol:
        query = query.filter(TechnicalIndicator.symbol == symbol)

    if start_date:
        query = query.filter(TechnicalIndicator.timestamp >= start_date)

    if end_date:
        query = query.filter(TechnicalIndicator.timestamp <= end_date)

    # Filter by indicator type if specified
    if indicator_type:
        indicator_type = indicator_type.lower()
        if indicator_type == "trend":
            query = query.filter(
                (TechnicalIndicator.sma_20.isnot(None))
                | (TechnicalIndicator.ema_12.isnot(None))
            )
        elif indicator_type == "momentum":
            query = query.filter(
                (TechnicalIndicator.rsi_14.isnot(None))
                | (TechnicalIndicator.macd.isnot(None))
                | (TechnicalIndicator.macd_signal.isnot(None))
                | (TechnicalIndicator.macd_histogram.isnot(None))
            )
        elif indicator_type == "volatility":
            query = query.filter(
                (TechnicalIndicator.bb_upper.isnot(None))
                | (TechnicalIndicator.bb_middle.isnot(None))
                | (TechnicalIndicator.bb_lower.isnot(None))
                | (TechnicalIndicator.atr_14.isnot(None))
            )

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    indicators = (
        query.order_by(desc(TechnicalIndicator.timestamp))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return IndicatorListResponse(
        success=True,
        data=indicators,
        count=len(indicators),
        total=total,
        message=f"Retrieved {len(indicators)} indicator records",
    )


@router.get("/indicators/{symbol}", response_model=IndicatorListResponse)
async def get_indicators_by_symbol(
    symbol: str,
    days: Optional[int] = Query(
        7, ge=1, le=365, description="Number of days of history to return"
    ),
    limit: Optional[int] = Query(
        None, ge=1, le=1000, description="Maximum records to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Get technical indicator history for a specific trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        days: Number of days of history (default: 7)
        limit: Maximum records to return
        db: Database session

    Returns:
        IndicatorListResponse: Indicator history for the symbol
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Build query
    query = (
        db.query(TechnicalIndicator)
        .filter(
            and_(
                TechnicalIndicator.symbol == symbol,
                TechnicalIndicator.timestamp >= start_date,
                TechnicalIndicator.timestamp <= end_date,
            )
        )
        .order_by(desc(TechnicalIndicator.timestamp))
    )

    # Get total count
    total = query.count()

    # Apply limit if specified
    if limit:
        indicators = query.limit(limit).all()
    else:
        indicators = query.all()

    return IndicatorListResponse(
        success=True,
        data=indicators,
        count=len(indicators),
        total=total,
        message=f"Retrieved {len(indicators)} indicator records for {symbol}",
    )


@router.get("/indicators/{symbol}/latest", response_model=IndicatorResponse)
async def get_latest_indicator(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Get the latest technical indicators for a trading pair.

    Args:
        symbol: Trading pair symbol
        db: Database session

    Returns:
        IndicatorResponse: Latest indicator record

    Raises:
        HTTPException: 404 if no indicators found for symbol
    """
    indicator = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.symbol == symbol)
        .order_by(desc(TechnicalIndicator.timestamp))
        .first()
    )

    if not indicator:
        raise HTTPException(
            status_code=404,
            detail=f"No technical indicator data found for symbol: {symbol}",
        )

    return IndicatorResponse(
        success=True,
        data=indicator,
        message=f"Latest technical indicators for {symbol}",
    )


@router.post("/indicators", response_model=IndicatorResponse)
async def create_indicator(
    indicator_data: IndicatorCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new technical indicator record with Decimal precision enforcement.

    Args:
        indicator_data: Indicator data with Decimal values
        db: Database session

    Returns:
        IndicatorResponse: Created indicator record

    Note:
        This endpoint enforces Decimal types - Float values will be rejected
        by Pydantic validation.
    """
    # Convert Pydantic model to SQLAlchemy model
    db_indicator = TechnicalIndicator(
        symbol=indicator_data.symbol,
        timestamp=indicator_data.timestamp,
        sma_20=indicator_data.sma_20,
        ema_12=indicator_data.ema_12,
        rsi_14=indicator_data.rsi_14,
        macd=indicator_data.macd,
        macd_signal=indicator_data.macd_signal,
        macd_histogram=indicator_data.macd_histogram,
        bb_upper=indicator_data.bb_upper,
        bb_middle=indicator_data.bb_middle,
        bb_lower=indicator_data.bb_lower,
        atr_14=indicator_data.atr_14,
    )

    # Save to database
    db.add(db_indicator)
    db.commit()
    db.refresh(db_indicator)

    return IndicatorResponse(
        success=True,
        data=db_indicator,
        message="Technical indicator record created successfully",
    )


@router.get("/indicators/{symbol}/stats")
async def get_indicator_stats(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
):
    """
    Get technical indicator statistics for a trading pair.

    Args:
        symbol: Trading pair symbol
        days: Number of days for statistics
        db: Database session

    Returns:
        IndicatorStatsResponse: Indicator statistics with Decimal precision
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get indicators in date range
    indicators = (
        db.query(TechnicalIndicator)
        .filter(
            and_(
                TechnicalIndicator.symbol == symbol,
                TechnicalIndicator.timestamp >= start_date,
                TechnicalIndicator.timestamp <= end_date,
            )
        )
        .order_by(TechnicalIndicator.timestamp)
        .all()
    )

    if not indicators:
        raise HTTPException(
            status_code=404,
            detail=f"No indicator data found for symbol {symbol} in the last {days} days",
        )

    # Initialize summary dictionary
    indicators_summary = {}

    # Define indicator fields to analyze
    indicator_fields = [
        ("sma_20", "Simple Moving Average (20)"),
        ("ema_12", "Exponential Moving Average (12)"),
        ("rsi_14", "Relative Strength Index (14)"),
        ("macd", "MACD Line"),
        ("macd_signal", "MACD Signal"),
        ("macd_histogram", "MACD Histogram"),
        ("bb_upper", "Bollinger Band Upper"),
        ("bb_middle", "Bollinger Band Middle"),
        ("bb_lower", "Bollinger Band Lower"),
        ("atr_14", "Average True Range (14)"),
    ]

    # Calculate statistics for each indicator
    for field_name, display_name in indicator_fields:
        # Extract non-None values
        values = [
            getattr(ind, field_name)
            for ind in indicators
            if getattr(ind, field_name) is not None
        ]

        if values:
            # Convert to Decimal for calculations
            decimal_values = [Decimal(str(v)) for v in values]

            # Calculate statistics
            min_val = min(decimal_values)
            max_val = max(decimal_values)
            latest_val = decimal_values[-1] if decimal_values else None

            # Calculate average
            avg_val = sum(decimal_values, Decimal("0")) / Decimal(
                str(len(decimal_values))
            )

            indicators_summary[field_name] = {
                "display_name": display_name,
                "record_count": len(values),
                "latest": str(latest_val) if latest_val else None,
                "minimum": str(min_val),
                "maximum": str(max_val),
                "average": str(avg_val.quantize(Decimal("0.00000001"))),
                "range": str(max_val - min_val),
            }
        else:
            indicators_summary[field_name] = {
                "display_name": display_name,
                "record_count": 0,
                "latest": None,
                "minimum": None,
                "maximum": None,
                "average": None,
                "range": None,
            }

    return IndicatorStatsResponse(
        symbol=symbol,
        period_days=days,
        record_count=len(indicators),
        date_range={
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        indicators_summary=indicators_summary,
        timestamp=datetime.utcnow(),
    )
