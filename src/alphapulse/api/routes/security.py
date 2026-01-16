"""
Security Operations (SecOps) endpoints.
"""

from fastapi import APIRouter, Depends
from typing import List

from alphapulse.api.schemas.security import AccessLogsResponse, AccessLog
from alphapulse.api.models_user import User
from alphapulse.security.auth import get_current_user_from_token, require_permission

router = APIRouter(prefix="/security", tags=["security"])

@router.get("/access-logs", response_model=AccessLogsResponse)
async def get_access_logs(
    current_user: User = Depends(require_permission("system:monitor")) # Assuming a monitor permission or similar
):
    """
    Get recent access logs for the Threat Map visualization.
    """
    # Mock data for demonstration
    return AccessLogsResponse(
        data=[
            AccessLog(ip="203.0.113.1", country="US", lat=37.77, lon=-122.41, status="allow"),
            AccessLog(ip="198.51.100.2", country="CN", lat=39.90, lon=116.40, status="block"),
            AccessLog(ip="185.199.108.153", country="DE", lat=51.16, lon=10.45, status="allow"),
            AccessLog(ip="140.82.113.3", country="US", lat=40.71, lon=-74.00, status="allow"),
             AccessLog(ip="103.21.244.0", country="RU", lat=55.75, lon=37.61, status="block"),
        ]
    )
