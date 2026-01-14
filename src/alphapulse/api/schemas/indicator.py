"""
Pydantic schemas for technical indicators with Decimal precision.

All indicator values use Decimal types to ensure exact precision
for financial calculations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class IndicatorBase(BaseModel):
    """Base schema for technical indicators."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTC-USD')")
    timestamp: datetime = Field(
        ..., description="Timestamp of the indicator calculation"
    )

    # Trend indicators
    sma_20: Optional[Decimal] = Field(
        None, description="Simple Moving Average (20 period)"
    )
    ema_12: Optional[Decimal] = Field(
        None, description="Exponential Moving Average (12 period)"
    )

    # Momentum indicators
    rsi_14: Optional[Decimal] = Field(
        None,
        description="Relative Strength Index (14 period)",
        ge=Decimal("0"),
        le=Decimal("100"),
    )
    macd: Optional[Decimal] = Field(None, description="MACD line")
    macd_signal: Optional[Decimal] = Field(None, description="MACD signal line")
    macd_histogram: Optional[Decimal] = Field(None, description="MACD histogram")

    # Volatility indicators
    bb_upper: Optional[Decimal] = Field(None, description="Bollinger Band upper band")
    bb_middle: Optional[Decimal] = Field(None, description="Bollinger Band middle band")
    bb_lower: Optional[Decimal] = Field(None, description="Bollinger Band lower band")
    atr_14: Optional[Decimal] = Field(
        None, description="Average True Range (14 period)", ge=Decimal("0")
    )

    @validator(
        "sma_20",
        "ema_12",
        "macd",
        "macd_signal",
        "macd_histogram",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "atr_14",
    )
    def validate_price_based_indicators(cls, v):
        """Validate price-based indicators."""
        if v is not None and v < Decimal("0"):
            raise ValueError("Price-based indicators cannot be negative")
        return v


class IndicatorCreate(IndicatorBase):
    """Schema for creating a new technical indicator record."""

    pass


class IndicatorData(IndicatorBase):
    """Schema for technical indicator data with ID."""

    id: int = Field(..., description="Unique identifier")

    class Config:
        """Pydantic configuration."""

        orm_mode = True
        json_encoders = {Decimal: str}


class IndicatorResponse(BaseModel):
    """Response schema for single technical indicator."""

    success: bool = Field(..., description="Request success status")
    data: IndicatorData = Field(..., description="Indicator data")
    message: Optional[str] = Field(None, description="Response message")


class IndicatorListResponse(BaseModel):
    """Response schema for list of technical indicators."""

    success: bool = Field(..., description="Request success status")
    data: list[IndicatorData] = Field(..., description="List of indicator records")
    count: int = Field(..., description="Number of records returned")
    total: int = Field(..., description="Total number of records available")
    message: Optional[str] = Field(None, description="Response message")


class IndicatorStatsResponse(BaseModel):
    """Response schema for indicator statistics."""

    symbol: str = Field(..., description="Trading pair symbol")
    period_days: int = Field(..., description="Number of days in the period")
    record_count: int = Field(..., description="Number of indicator records")
    date_range: dict = Field(..., description="Start and end dates of the period")
    indicators_summary: dict = Field(
        ..., description="Summary statistics for each indicator"
    )
    timestamp: datetime = Field(..., description="Response timestamp")
