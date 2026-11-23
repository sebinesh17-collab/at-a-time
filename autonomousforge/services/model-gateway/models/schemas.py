"""
Model Gateway models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ProviderCreate(BaseModel):
    name: str
    provider_type: str  # openai, anthropic, nvidia, custom
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: bool = True
    models: List[str] = []
    weight: int = Field(default=100, ge=1, le=1000)
    concurrency_limit: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    retry_config: Dict[str, Any] = {}


class ProviderUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    models: Optional[List[str]] = None
    weight: Optional[int] = None
    concurrency_limit: Optional[int] = None
    timeout_seconds: Optional[int] = None
    retry_config: Optional[Dict[str, Any]] = None


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
    health_status: str
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelCreate(BaseModel):
    provider_id: UUID
    model_id: str
    display_name: str
    capabilities: List[str] = []  # chat, completion, embedding, vision, function_calling
    context_window: int = 4096
    max_output_tokens: int = 2048
    pricing_input: Optional[float] = None  # per 1M tokens
    pricing_output: Optional[float] = None
    is_enabled: bool = True
    metadata: Dict[str, Any] = {}


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


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    user: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    system_fingerprint: Optional[str] = None


class EmbeddingRequest(BaseModel):
    model: str
    input: List[str] | str
    encoding_format: str = "float"
    dimensions: Optional[int] = None
    user: Optional[str] = None


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[Dict[str, Any]]
    model: str
    usage: Dict[str, int]


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelResponse]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    providers_healthy: int
    providers_total: int