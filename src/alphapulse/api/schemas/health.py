from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HealthStatus(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database: Optional[str] = None
    redis: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(json_encoders={datetime: lambda value: value.isoformat()})


class HealthDetailed(BaseModel):
    overall: str
    components: dict[str, str]
    timestamp: datetime
    uptime: Optional[float] = None
    message: Optional[str] = None

    model_config = ConfigDict(json_encoders={datetime: lambda value: value.isoformat()})
