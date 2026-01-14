"""
Pydantic schemas for AlphaPulse API.

These schemas enforce Decimal precision for all financial data,
ensuring no Float types are used in monetary calculations.
"""

from .health import HealthStatus
from .indicator import (
    IndicatorBase,
    IndicatorCreate,
    IndicatorData,
    IndicatorListResponse,
    IndicatorResponse,
    IndicatorStatsResponse,
)
from .price import PriceCreate, PriceData, PriceResponse
from .signal import SignalCreate, SignalResponse, TradingSignal

__all__ = [
    "PriceData",
    "PriceCreate",
    "PriceResponse",
    "TradingSignal",
    "SignalCreate",
    "SignalResponse",
    "HealthStatus",
    "IndicatorBase",
    "IndicatorCreate",
    "IndicatorData",
    "IndicatorListResponse",
    "IndicatorResponse",
    "IndicatorStatsResponse",
]
