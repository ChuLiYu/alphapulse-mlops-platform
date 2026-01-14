"""
Trading signal schemas with Decimal precision enforcement.

Critical: All confidence scores use Decimal (0.0000 to 1.0000),
not Float, to prevent floating-point precision errors.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


class SignalBase(BaseModel):
    """Base schema for trading signals with Decimal enforcement."""

    symbol: str = Field(..., example="BTC-USD", description="Trading pair symbol")
    signal_type: Literal["BUY", "SELL", "HOLD"] = Field(
        ..., example="BUY", description="Trading signal type"
    )
    confidence: Decimal = Field(
        ...,
        example=Decimal("0.8750"),
        description="Confidence score (0.0000 to 1.0000) with Decimal precision",
    )
    timestamp: datetime = Field(
        ...,
        example="2026-01-10T21:55:00Z",
        description="Timestamp when the signal was generated",
    )
    price_at_signal: Optional[Decimal] = Field(
        None,
        example=Decimal("45123.50"),
        description="Price at the time of signal generation (Decimal precision)",
    )

    @validator("confidence")
    def validate_confidence_range(cls, v):
        """Validate confidence is between 0.0000 and 1.0000."""
        if not isinstance(v, Decimal):
            raise ValueError(f"Expected Decimal for confidence, got {type(v).__name__}")

        if v < Decimal("0.0000") or v > Decimal("1.0000"):
            raise ValueError(f"Confidence must be between 0.0000 and 1.0000, got {v}")

        # Ensure 4 decimal places precision
        v = v.quantize(Decimal("0.0001"))
        return v

    @validator("price_at_signal")
    def validate_price_precision(cls, v):
        """Validate price precision if provided."""
        if v is not None and not isinstance(v, Decimal):
            raise ValueError(f"Expected Decimal for price, got {type(v).__name__}")

        if v is not None:
            # Ensure 8 decimal places for price
            v = v.quantize(Decimal("0.00000001"))
        return v

    class Config:
        """Pydantic configuration for Decimal handling."""

        json_encoders = {
            Decimal: lambda v: str(v),  # Serialize Decimal as string
            datetime: lambda v: v.isoformat(),
        }
        schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "signal_type": "BUY",
                "confidence": "0.8750",
                "timestamp": "2026-01-10T21:55:00Z",
                "price_at_signal": "45123.50",
            }
        }


class SignalCreate(SignalBase):
    """Schema for creating new trading signals."""

    pass


class TradingSignal(SignalBase):
    """Schema for trading signal response (includes ID)."""

    id: int = Field(
        ..., example=1, description="Unique identifier for the signal record"
    )

    class Config:
        """Pydantic configuration for response schema."""

        orm_mode = True


class SignalResponse(BaseModel):
    """Response wrapper for trading signal data."""

    success: bool = Field(..., example=True, description="Request success status")
    data: Optional[TradingSignal] = Field(None, description="Trading signal data")
    message: Optional[str] = Field(None, example="Signal retrieved successfully")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: lambda v: str(v), datetime: lambda v: v.isoformat()}


class SignalListResponse(BaseModel):
    """Response wrapper for multiple trading signals."""

    success: bool = Field(..., example=True, description="Request success status")
    data: list[TradingSignal] = Field(..., description="List of trading signals")
    count: int = Field(..., example=10, description="Number of signals returned")
    total: Optional[int] = Field(
        None, example=100, description="Total signals available"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: lambda v: str(v), datetime: lambda v: v.isoformat()}


class SignalStats(BaseModel):
    """Statistics about trading signals."""

    total_signals: int = Field(..., example=100, description="Total number of signals")
    buy_signals: int = Field(..., example=45, description="Number of BUY signals")
    sell_signals: int = Field(..., example=35, description="Number of SELL signals")
    hold_signals: int = Field(..., example=20, description="Number of HOLD signals")
    avg_confidence: Decimal = Field(
        ...,
        example=Decimal("0.7250"),
        description="Average confidence score (Decimal precision)",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: lambda v: str(v)}
