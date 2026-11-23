"""
Monitoring Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class MetricCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: float
    metric_type: str = Field(default="gauge")  # counter, gauge, histogram, summary
    labels: Dict[str, str] = {}
    timestamp: Optional[datetime] = None


class MetricBatchCreate(BaseModel):
    metrics: List[MetricCreate]


class MetricResponse(BaseModel):
    id: UUID
    name: str
    value: float
    metric_type: str
    labels: Dict[str, str]
    timestamp: datetime

    class Config:
        from_attributes = True


class MetricQuery(BaseModel):
    name: str
    labels: Optional[Dict[str, str]] = None
    start_time: datetime
    end_time: datetime
    step_seconds: int = 60
    aggregation: str = "avg"  # avg, sum, min, max, count


class MetricDataPoint(BaseModel):
    timestamp: datetime
    value: float


class MetricQueryResponse(BaseModel):
    name: str
    labels: Dict[str, str]
    data_points: List[MetricDataPoint]
    aggregation: str


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    metric_name: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    evaluation_window_seconds: int = Field(default=300, ge=60, le=86400)
    severity: str = Field(default="warning")  # info, warning, critical
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    is_enabled: bool = True


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    evaluation_window_seconds: Optional[int] = None
    severity: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    is_enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    metric_name: str
    condition: str
    threshold: float
    evaluation_window_seconds: int
    severity: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    is_enabled: bool
    last_evaluation: Optional[datetime]
    last_triggered: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    rule_id: UUID
    labels: Dict[str, str] = {}
    value: float


class AlertResponse(BaseModel):
    id: UUID
    rule_id: UUID
    rule_name: str
    severity: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    value: float
    threshold: float
    status: str  # firing, resolved, acknowledged
    started_at: datetime
    resolved_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True


class AlertFilter(BaseModel):
    rule_id: Optional[UUID] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class ServiceHealthCreate(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., pattern=r'^(healthy|degraded|unhealthy)$')
    latency_ms: Optional[int] = None
    error_rate: Optional[float] = None
    details: Dict[str, Any] = {}


class ServiceHealthResponse(BaseModel):
    service_name: str
    status: str
    latency_ms: Optional[int]
    error_rate: Optional[float]
    details: Dict[str, Any]
    last_check: datetime
    uptime_percentage: float

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    layout: List[Dict[str, Any]] = []
    is_default: bool = False


class DashboardResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    layout: List[Dict[str, Any]]
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    active_alerts: int
    monitored_services: int