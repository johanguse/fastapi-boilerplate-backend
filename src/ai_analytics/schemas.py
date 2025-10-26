"""AI Analytics schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AIAnalyticsQueryCreate(BaseModel):
    """Schema for creating AI analytics queries."""
    natural_query: str = Field(..., min_length=1, max_length=1000)


class AIAnalyticsQueryResponse(BaseModel):
    """Schema for AI analytics query responses."""
    id: int
    organization_id: int
    user_id: int
    natural_query: str
    sql_query: Optional[str]
    results: Dict[str, Any]
    chart_config: Dict[str, Any]
    status: str
    error_message: Optional[str]
    tokens_used: int
    cost: float
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsInsightResponse(BaseModel):
    """Schema for analytics insights."""
    insight: str
    chart_type: str
    data: Dict[str, Any]
    recommendations: List[str]


class AnalyticsQueryRequest(BaseModel):
    """Schema for analytics query requests."""
    query: str = Field(..., min_length=1, max_length=1000)
    chart_type: Optional[str] = Field(None, max_length=50)  # bar, line, pie, table
    time_range: Optional[str] = Field(None, max_length=50)  # last_7_days, last_30_days, etc.


class AnalyticsQueryResponse(BaseModel):
    """Schema for analytics query responses."""
    query_id: int
    results: Dict[str, Any]
    chart_config: Dict[str, Any]
    insights: List[AnalyticsInsightResponse]
    tokens_used: int
    cost: float


class ChartConfig(BaseModel):
    """Schema for chart configuration."""
    type: str = Field(..., max_length=50)  # bar, line, pie, table
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    data: List[Dict[str, Any]]
    options: Dict[str, Any] = Field(default_factory=dict)
