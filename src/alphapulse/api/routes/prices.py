"""
Price data endpoints with Decimal precision enforcement.

All monetary values use Decimal types to prevent floating-point
precision errors in financial calculations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from alphapulse.api.database import get_db
from alphapulse.api.models import Price
from alphapulse.api.schemas.price import (
    PriceCreate,
    PriceData,
    PriceListResponse,
    PriceResponse,
)

router = APIRouter()


@router.get("/prices", response_model=PriceListResponse)
async def get_prices(
    symbol: Optional[str] = Query(None, description="Filter by trading pair symbol"),
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
    Get historical price data with Decimal precision.

    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        start_date: Start of time range
        end_date: End of time range
        limit: Maximum records to return (1-1000)
        offset: Records to skip (for pagination)
        db: Database session

    Returns:
        PriceListResponse: List of price records with Decimal values
    """
    # Build query
    query = db.query(Price)

    # Apply filters
    if symbol:
        query = query.filter(Price.symbol == symbol)

    if start_date:
        query = query.filter(Price.timestamp >= start_date)

    if end_date:
        query = query.filter(Price.timestamp <= end_date)

    # Get total count before pagination
    total = query.count()

    # Apply ordering and pagination
    prices = query.order_by(desc(Price.timestamp)).offset(offset).limit(limit).all()

    return PriceListResponse(
        success=True,
        data=prices,
        count=len(prices),
        total=total,
    )


@router.get("/prices/{symbol}", response_model=PriceListResponse)
async def get_prices_by_symbol(
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
    Get price history for a specific trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        days: Number of days of history (default: 7)
        limit: Maximum records to return
        db: Database session

    Returns:
        PriceListResponse: Price history for the symbol
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Build query
    query = (
        db.query(Price)
        .filter(
            and_(
                Price.symbol == symbol,
                Price.timestamp >= start_date,
                Price.timestamp <= end_date,
            )
        )
        .order_by(desc(Price.timestamp))
    )

    # Get total count
    total = query.count()

    # Apply limit if specified
    if limit:
        prices = query.limit(limit).all()
    else:
        prices = query.all()

    return PriceListResponse(
        success=True,
        data=prices,
        count=len(prices),
        total=total,
    )


@router.get("/prices/{symbol}/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Get the latest price for a trading pair.

    Args:
        symbol: Trading pair symbol
        db: Database session

    Returns:
        PriceResponse: Latest price record

    Raises:
        HTTPException: 404 if no price found for symbol
    """
    price = (
        db.query(Price)
        .filter(Price.symbol == symbol)
        .order_by(desc(Price.timestamp))
        .first()
    )

    if not price:
        raise HTTPException(
            status_code=404, detail=f"No price data found for symbol: {symbol}"
        )

    return PriceResponse(success=True, data=price, message=f"Latest price for {symbol}")


@router.post("/prices", response_model=PriceResponse)
async def create_price(
    price_data: PriceCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new price record with Decimal precision enforcement.

    Args:
        price_data: Price data with Decimal values
        db: Database session

    Returns:
        PriceResponse: Created price record

    Note:
        This endpoint enforces Decimal types - Float values will be rejected
        by Pydantic validation.
    """
    # Convert Pydantic model to SQLAlchemy model
    db_price = Price(
        symbol=price_data.symbol,
        price=price_data.price,
        volume=price_data.volume,
        timestamp=price_data.timestamp,
    )

    # Save to database
    db.add(db_price)
    db.commit()
    db.refresh(db_price)

    return PriceResponse(
        success=True, data=db_price, message="Price record created successfully"
    )


@router.get("/prices/{symbol}/stats")
async def get_price_stats(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    db: Session = Depends(get_db),
):
    """
    Get price statistics for a trading pair.

    Args:
        symbol: Trading pair symbol
        days: Number of days for statistics
        db: Database session

    Returns:
        dict: Price statistics with Decimal precision
    """
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get prices in date range
    prices = (
        db.query(Price)
        .filter(
            and_(
                Price.symbol == symbol,
                Price.timestamp >= start_date,
                Price.timestamp <= end_date,
            )
        )
        .order_by(Price.timestamp)
        .all()
    )

    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for symbol {symbol} in the last {days} days",
        )

    # Extract price values as Decimal
    price_values = [p.price for p in prices]

    # Calculate statistics with Decimal precision
    if price_values:
        min_price = min(price_values)
        max_price = max(price_values)
        latest_price = price_values[-1]

        # Calculate average (need to convert to float for mean, then back to Decimal)
        avg_price = sum(price_values, Decimal("0")) / Decimal(str(len(price_values)))

        # Calculate price change
        if len(price_values) >= 2:
            first_price = price_values[0]
            price_change = latest_price - first_price
            price_change_pct = (price_change / first_price) * Decimal("100")
        else:
            price_change = Decimal("0")
            price_change_pct = Decimal("0")
    else:
        min_price = max_price = latest_price = avg_price = Decimal("0")
        price_change = price_change_pct = Decimal("0")

    return {
        "symbol": symbol,
        "period_days": days,
        "record_count": len(prices),
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "prices": {
            "latest": str(latest_price),
            "minimum": str(min_price),
            "maximum": str(max_price),
            "average": str(avg_price.quantize(Decimal("0.00000001"))),
        },
        "changes": {
            "absolute": str(price_change),
            "percentage": str(price_change_pct.quantize(Decimal("0.01"))),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
