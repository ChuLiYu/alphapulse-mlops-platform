"""
Trading signal endpoints with Decimal precision enforcement.

All confidence scores use Decimal types (0.0000 to 1.0000) to prevent
floating-point precision errors in financial calculations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from src.alphapulse.api.database import get_db
from src.alphapulse.api.models import TradingSignal
from src.alphapulse.api.schemas.signal import (
    SignalCreate,
    SignalListResponse,
    SignalResponse,
    SignalStats,
)
from src.alphapulse.api.schemas.signal import TradingSignal as TradingSignalSchema

router = APIRouter()


@router.get("/signals", response_model=SignalListResponse)
async def get_signals(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol"),
    signal_type: Optional[str] = Query(
        None, description="Filter by signal type (BUY/SELL/HOLD)"
    ),
    min_confidence: Optional[Decimal] = Query(
        None,
        ge=Decimal("0.0000"),
        le=Decimal("1.0000"),
        description="Minimum confidence score (0.0000 to 1.0000)",
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date for time range"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for time range"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db),
):
    """
    Get trading signals with Decimal precision confidence scores.

    Args:
        symbol: Trading pair symbol
        signal_type: Signal type (BUY/SELL/HOLD)
        min_confidence: Minimum confidence score
        start_date: Start of time range
        end_date: End of time range
        limit: Maximum records to return
        offset: Records to skip
        db: Database session

    Returns:
        SignalListResponse: List of trading signals
    """
    # Build query
    query = db.query(TradingSignal)

    # Apply filters
    if symbol:
        query = query.filter(TradingSignal.symbol == symbol)

    if signal_type:
        query = query.filter(TradingSignal.signal_type == signal_type)

    if min_confidence is not None:
        query = query.filter(TradingSignal.confidence >= min_confidence)

    if start_date:
        query = query.filter(TradingSignal.timestamp >= start_date)

    if end_date:
        query = query.filter(TradingSignal.timestamp <= end_date)

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    signals = (
        query.order_by(desc(TradingSignal.timestamp)).offset(offset).limit(limit).all()
    )

    return SignalListResponse(
        success=True,
        data=signals,
        count=len(signals),
        total=total,
    )


@router.get("/signals/{symbol}", response_model=SignalListResponse)
async def get_signals_by_symbol(
    symbol: str,
    days: Optional[int] = Query(
        7, ge=1, le=365, description="Number of days of history"
    ),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    limit: Optional[int] = Query(
        None, ge=1, le=1000, description="Maximum records to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Get trading signals for a specific trading pair.

    Args:
        symbol: Trading pair symbol
        days: Number of days of history
        signal_type: Filter by signal type
        limit: Maximum records to return
        db: Database session

    Returns:
        SignalListResponse: Trading signals for the symbol
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Build query
    query = db.query(TradingSignal).filter(
        and_(
            TradingSignal.symbol == symbol,
            TradingSignal.timestamp >= start_date,
            TradingSignal.timestamp <= end_date,
        )
    )

    # Apply signal type filter if specified
    if signal_type:
        query = query.filter(TradingSignal.signal_type == signal_type)

    # Order by timestamp (newest first)
    query = query.order_by(desc(TradingSignal.timestamp))

    # Get total count
    total = query.count()

    # Apply limit if specified
    if limit:
        signals = query.limit(limit).all()
    else:
        signals = query.all()

    return SignalListResponse(
        success=True,
        data=signals,
        count=len(signals),
        total=total,
    )


@router.get("/signals/{symbol}/latest", response_model=SignalResponse)
async def get_latest_signal(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Get the latest trading signal for a trading pair.

    Args:
        symbol: Trading pair symbol
        db: Database session

    Returns:
        SignalResponse: Latest trading signal

    Raises:
        HTTPException: 404 if no signal found for symbol
    """
    signal = (
        db.query(TradingSignal)
        .filter(TradingSignal.symbol == symbol)
        .order_by(desc(TradingSignal.timestamp))
        .first()
    )

    if not signal:
        raise HTTPException(
            status_code=404, detail=f"No trading signals found for symbol: {symbol}"
        )

    return SignalResponse(
        success=True, data=signal, message=f"Latest signal for {symbol}"
    )


@router.post("/signals", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new trading signal with Decimal precision enforcement.

    Args:
        signal_data: Trading signal data with Decimal confidence
        db: Database session

    Returns:
        SignalResponse: Created trading signal

    Note:
        Confidence scores must be Decimal between 0.0000 and 1.0000
    """
    # Convert Pydantic model to SQLAlchemy model
    db_signal = TradingSignal(
        symbol=signal_data.symbol,
        signal_type=signal_data.signal_type,
        confidence=signal_data.confidence,
        price_at_signal=signal_data.price_at_signal,
        timestamp=signal_data.timestamp,
    )

    # Save to database
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)

    return SignalResponse(
        success=True, data=db_signal, message="Trading signal created successfully"
    )


@router.get("/signals/{symbol}/stats", response_model=SignalStats)
async def get_signal_stats(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
):
    """
    Get trading signal statistics for a trading pair.

    Args:
        symbol: Trading pair symbol
        days: Number of days for statistics
        db: Database session

    Returns:
        SignalStats: Signal statistics with Decimal precision
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get signals in date range
    signals = (
        db.query(TradingSignal)
        .filter(
            and_(
                TradingSignal.symbol == symbol,
                TradingSignal.timestamp >= start_date,
                TradingSignal.timestamp <= end_date,
            )
        )
        .all()
    )

    if not signals:
        raise HTTPException(
            status_code=404,
            detail=f"No trading signals found for symbol {symbol} in the last {days} days",
        )

    # Calculate statistics
    total_signals = len(signals)
    buy_signals = sum(1 for s in signals if s.signal_type == "BUY")
    sell_signals = sum(1 for s in signals if s.signal_type == "SELL")
    hold_signals = sum(1 for s in signals if s.signal_type == "HOLD")

    # Calculate average confidence with Decimal precision
    if signals:
        total_confidence = sum(s.confidence for s in signals)
        avg_confidence = total_confidence / Decimal(str(total_signals))
    else:
        avg_confidence = Decimal("0.0000")

    return SignalStats(
        total_signals=total_signals,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        hold_signals=hold_signals,
        avg_confidence=avg_confidence.quantize(Decimal("0.0001")),
    )


@router.get("/signals/analysis/recent-performance")
async def get_recent_signal_performance(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    min_confidence: Decimal = Query(
        Decimal("0.7000"),
        ge=Decimal("0.0000"),
        le=Decimal("1.0000"),
        description="Minimum confidence score to include",
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze recent signal performance.

    Args:
        days: Number of days to analyze
        min_confidence: Minimum confidence score
        db: Database session

    Returns:
        dict: Signal performance analysis
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get high-confidence signals
    signals = (
        db.query(TradingSignal)
        .filter(
            and_(
                TradingSignal.timestamp >= start_date,
                TradingSignal.timestamp <= end_date,
                TradingSignal.confidence >= min_confidence,
            )
        )
        .all()
    )

    # Group by signal type
    signal_types = {}
    for signal in signals:
        if signal.signal_type not in signal_types:
            signal_types[signal.signal_type] = []
        signal_types[signal.signal_type].append(signal)

    # Calculate performance metrics
    analysis = {
        "analysis_period_days": days,
        "min_confidence": str(min_confidence),
        "total_signals_analyzed": len(signals),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "by_signal_type": {},
        "summary": {
            "most_common_signal": None,
            "highest_confidence_signal": None,
            "average_confidence": "0.0000",
        },
    }

    if signals:
        # Calculate by signal type
        for signal_type, type_signals in signal_types.items():
            confidences = [s.confidence for s in type_signals]
            avg_confidence = sum(confidences, Decimal("0")) / Decimal(
                str(len(confidences))
            )

            analysis["by_signal_type"][signal_type] = {
                "count": len(type_signals),
                "percentage": f"{(len(type_signals) / len(signals) * 100):.2f}%",
                "average_confidence": str(avg_confidence.quantize(Decimal("0.0001"))),
                "min_confidence": str(min(confidences).quantize(Decimal("0.0001"))),
                "max_confidence": str(max(confidences).quantize(Decimal("0.0001"))),
            }

        # Find most common signal type
        most_common = max(signal_types.items(), key=lambda x: len(x[1]))[0]

        # Find highest confidence signal
        highest_confidence_signal = max(signals, key=lambda x: x.confidence)

        # Calculate overall average confidence
        overall_avg = sum(s.confidence for s in signals) / Decimal(str(len(signals)))

        analysis["summary"] = {
            "most_common_signal": most_common,
            "highest_confidence_signal": {
                "id": highest_confidence_signal.id,
                "symbol": highest_confidence_signal.symbol,
                "signal_type": highest_confidence_signal.signal_type,
                "confidence": str(highest_confidence_signal.confidence),
                "timestamp": highest_confidence_signal.timestamp.isoformat(),
            },
            "average_confidence": str(overall_avg.quantize(Decimal("0.0001"))),
        }

    return analysis
