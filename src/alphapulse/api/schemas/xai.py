"""
Explainable AI (XAI) schemas for trading signal transparency.
"""

from typing import List

from pydantic import BaseModel


class FeatureImportance(BaseModel):
    """Contribution of a single feature to the model's decision."""

    feature: str
    impact: float
    description: str


class SignalExplanationResponse(BaseModel):
    """Response containing the explanation for a specific signal."""

    signal_id: int
    feature_importance: List[FeatureImportance]
    llm_summary: str
