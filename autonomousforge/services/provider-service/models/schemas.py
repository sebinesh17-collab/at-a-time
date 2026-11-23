"""
Provider Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., pattern=r'^(openai|anthropic|nvidia|custom)$')
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: bool = True
    models: List[str] = []
    weight: int = Field(default=100, ge=1, le=1000)
    concurrency_limit: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    retry_config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    models: Optional[List[str]] = None
    weight: Optional[int] = Field(None, ge=1, le=1000)
    concurrency_limit: Optional[int] = Field(None, ge=1, le=100)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    retry_config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ProviderResponse(BaseModel):
    id: UUID
    name: str
    provider_type: str
    base_url: Optional[str]
    is_enabled: bool
    models: List[str]
    weight: int
    concurrency_limit: int
    timeout_seconds: int
    retry_config: Dict[str, Any]
    metadata: Dict[str, Any]
    health_status: str
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    provider_id: UUID
    model_id: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    capabilities: List[str] = Field(default_factory=list)  # chat, completion, embedding, vision, function_calling
    context_window: int = Field(default=4096, ge=1)
    max_output_tokens: int = Field(default=2048, ge=1)
    pricing_input: Optional[float] = None  # per 1M tokens
    pricing_output: Optional[float] = None
    is_enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    capabilities: Optional[List[str]] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    pricing_input: Optional[float] = None
    pricing_output: Optional[float] = None
    is_enabled: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    id: UUID
    provider_id: UUID
    model_id: str
    display_name: str
    capabilities: List[str]
    context_window: int
    max_output_tokens: int
    pricing_input: Optional[float]
    pricing_output: Optional[float]
    is_enabled: bool
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProviderHealthCheck(BaseModel):
    provider_id: UUID
    force: bool = False


class ProviderHealthResponse(BaseModel):
    provider_id: UUID
    provider_name: str
    health_status: str  # healthy, degraded, failed, unknown
    latency_ms: Optional[int]
    error_message: Optional[str]
    models_checked: int
    models_healthy: int
    checked_at: datetime


class ProviderFilter(BaseModel):
    provider_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    health_status: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class ModelFilter(BaseModel):
    provider_id: Optional[UUID] = None
    is_enabled: Optional[bool] = None
    capability: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class ProviderStatsResponse(BaseModel):
    total_providers: int
    providers_by_type: Dict[str, int]
    providers_by_health: Dict[str, int]
    total_models: int
    models_by_capability: Dict[str, int]
    healthy_providers: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    providers_healthy: int
    providers_total: int
    models_available: int