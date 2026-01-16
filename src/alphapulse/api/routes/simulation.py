"""
Simulation endpoints for the Strategy Playground.
"""

from fastapi import APIRouter, Depends, status
from typing import List
import random

from alphapulse.api.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    EquityPoint,
    SimulationMetrics
)
# Assuming auth dependency is needed, though not strictly specified for this public-ish demo feature
# using security.auth just to be safe or maybe open for now? 
# Specs say "Authentication: Bearer Token (JWT)" for all /api/v1.
from alphapulse.api.models_user import User
from alphapulse.security.auth import get_current_user_from_token

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/backtest", response_model=SimulationResponse)
async def run_backtest(
    request: SimulationRequest,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Run a quick interactive backtest simulation.
    
    This is currently a simulation/mock implementation for the frontend prototype.
    """
    
    # Realistic logic to generate an equity curve based on input
    days = 30
    equity = request.initial_capital
    curve = []
    
    # Introduce "Regime Shifts" (periods where model performs better or worse)
    regimes = [1.0, 0.8, 1.2, 0.5] # Multipliers for bias
    
    # Volatility and bias tuning
    volatility_map = {"low": 0.012, "medium": 0.025, "high": 0.06}
    bias_map = {"low": 0.0003, "medium": 0.0008, "high": 0.0015}
    
    volatility = volatility_map.get(request.risk_level, 0.025)
    base_bias = bias_map.get(request.risk_level, 0.0008)
    
    # Adjust bias by confidence threshold (diminishing returns after 0.85)
    confidence_impact = (request.confidence_threshold - 0.7) * 0.005
    
    for day in range(1, days + 1):
        # Change regime every 7-8 days to simulate market shifts
        current_regime = regimes[(day // 8) % len(regimes)]
        
        # Random daily return with regime-influenced bias
        change_pct = random.gauss(base_bias * current_regime + confidence_impact, volatility)
        
        # Simulation of "Bad Days" where the model completely misses a move
        if day in [5, 12, 22]:
            change_pct = -volatility * 1.5
            
        # Apply stop loss logic simulation
        if change_pct < -request.stop_loss_pct / 100:
            change_pct = -request.stop_loss_pct / 100
            
        equity *= (1 + change_pct)
        curve.append(EquityPoint(day=day, value=round(equity, 2)))
    
    total_return_pct = ((equity - request.initial_capital) / request.initial_capital) * 100
    
    # Generate realistic metrics for an "optimizing" model
    return SimulationResponse(
        equity_curve=curve,
        metrics=SimulationMetrics(
            total_return=round(total_return_pct, 2),
            # Max drawdown usually between 5% and 15% for these models
            max_drawdown=round(random.uniform(-15.0, -4.5), 2),
            # Sharpe ratio 1.0 - 1.7 is a "good but needs work" range
            sharpe_ratio=round(random.uniform(1.05, 1.65), 2)
        )
    )

