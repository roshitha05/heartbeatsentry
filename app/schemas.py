from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class EndpointCreate(BaseModel):
    name: str
    url: HttpUrl


class EndpointResponse(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckResponse(BaseModel):
    id: int
    endpoint_id: int
    status: str
    status_code: int | None
    response_time_ms: float
    error: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EndpointStatsResponse(BaseModel):
    endpoint_id: int
    endpoint_name: str
    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float
    average_response_time_ms: float
    latest_status: str | None