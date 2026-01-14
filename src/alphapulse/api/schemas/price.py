"""
Price data schemas with Decimal precision enforcement.

Critical: All monetary values use Decimal, not Float, to prevent
floating-point precision errors in financial calculations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class PriceBase(BaseModel):
    """Base schema for price data with Decimal enforcement."""

    symbol: str = Field(
        ...,
        example="BTC-USD",
        description="Trading pair symbol (e.g., BTC-USD, ETH-USD)",
    )
    price: Decimal = Field(
        ...,
        example=Decimal("45123.50"),
        description="Price in USD with Decimal precision (not Float)",
    )
    volume: Decimal = Field(
        ...,
        example=Decimal("1234567.89"),
        description="Trading volume with Decimal precision",
    )
    timestamp: datetime = Field(
        ..., example="2026-01-10T21:55:00Z", description="Timestamp of the price data"
    )

    @validator("price", "volume")
    def validate_decimal_precision(cls, v):
        """Validate that Decimal values have appropriate precision."""
        if not isinstance(v, Decimal):
            raise ValueError(f"Expected Decimal, got {type(v).__name__}")

        # Ensure reasonable precision for financial data
        # Price: up to 20 digits, 8 decimal places (supports up to 999,999,999.99999999)
        # Volume: up to 20 digits, 8 decimal places
        str_value = str(v)
        if "." in str_value:
            integer_part, decimal_part = str_value.split(".")
            if len(integer_part) > 12:  # 12 digits for integer part
                raise ValueError(f"Integer part too large: {integer_part}")
            if len(decimal_part) > 8:  # 8 decimal places
                # Round to 8 decimal places
                v = v.quantize(Decimal("0.00000001"))
        return v

    class Config:
        """Pydantic configuration for Decimal handling."""

        json_encoders = {
            Decimal: lambda v: str(v),  # Serialize Decimal as string
            datetime: lambda v: v.isoformat(),  # Serialize datetime as ISO string
        }
        schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "price": "45123.50",
                "volume": "1234567.89",
                "timestamp": "2026-01-10T21:55:00Z",
            }
        }


class PriceCreate(PriceBase):
    """Schema for creating new price data."""

    pass


class PriceData(PriceBase):
    """Schema for price data response (includes ID)."""

    id: int = Field(
        ..., example=1, description="Unique identifier for the price record"
    )

    class Config:
        """Pydantic configuration for response schema."""

        orm_mode = True


class PriceResponse(BaseModel):
    """Response wrapper for price data."""

    success: bool = Field(..., example=True, description="Request success status")
    data: Optional[PriceData] = Field(None, description="Price data")
    message: Optional[str] = Field(None, example="Price data retrieved successfully")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: lambda v: str(v), datetime: lambda v: v.isoformat()}


class PriceListResponse(BaseModel):
    """Response wrapper for multiple price records."""

    success: bool = Field(..., example=True, description="Request success status")
    data: list[PriceData] = Field(..., description="List of price records")
    count: int = Field(..., example=10, description="Number of records returned")
    total: Optional[int] = Field(
        None, example=100, description="Total records available"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: lambda v: str(v), datetime: lambda v: v.isoformat()}
