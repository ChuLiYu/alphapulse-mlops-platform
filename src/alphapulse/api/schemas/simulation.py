"""
Simulation schemas for the Strategy Playground.
"""

from decimal import Decimal
from typing import List, Literal

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    """Request schema for running a backtest simulation."""

    risk_level: Literal["low", "medium", "high"] = Field(
        ..., description="Risk tolerance level"
    )
    confidence_threshold: float = Field(
        ..., ge=0.5, le=0.99, description="Minimum model confidence to trade"
    )
    stop_loss_pct: float = Field(
        ..., ge=0.01, le=0.10, description="Stop loss percentage (0.01 - 0.10)"
    )
    initial_capital: float = Field(
        ..., gt=0, description="Initial capital for the simulation"
    )


class EquityPoint(BaseModel):
    """A single data point in the equity curve."""

    day: int
    value: float


class SimulationMetrics(BaseModel):
    """Key performance metrics from the simulation."""

    total_return: float
    max_drawdown: float
    sharpe_ratio: float


class SimulationResponse(BaseModel):
    """Response schema containing simulation results."""

    equity_curve: List[EquityPoint]
    metrics: SimulationMetrics
