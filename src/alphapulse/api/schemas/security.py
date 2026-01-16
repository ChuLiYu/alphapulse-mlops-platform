"""
Security schemas for the SecOps monitor and Threat Map.
"""

from typing import List, Literal

from pydantic import BaseModel


class AccessLog(BaseModel):
    """Represents a single access log entry for the Threat Map."""

    ip: str
    country: str
    lat: float
    lon: float
    status: Literal["allow", "block"]


class AccessLogsResponse(BaseModel):
    """Response wrapper for access logs."""

    data: List[AccessLog]
