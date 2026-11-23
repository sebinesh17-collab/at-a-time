"""
Memory Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class MemoryCreate(BaseModel):
    memory_type: str = Field(..., pattern=r'^(owner|conversation|project|agent|workflow|execution|technical_decision)$')
    project_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    key: str = Field(..., min_length=1, max_length=500)
    value: Dict[str, Any]
    importance: float = Field(default=1.0, ge=0.0, le=10.0)
    expires_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None


class MemoryUpdate(BaseModel):
    value: Optional[Dict[str, Any]] = None
    importance: Optional[float] = Field(None, ge=0.0, le=10.0)
    expires_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None


class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    owner_id: UUID
    project_id: Optional[UUID]
    agent_id: Optional[str]
    conversation_id: Optional[UUID]
    workflow_id: Optional[UUID]
    key: str
    value: Dict[str, Any]
    embedding: Optional[List[float]]
    importance: float
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    memory_type: Optional[str] = None
    project_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    query: Optional[str] = None
    key_pattern: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_expired: bool = False


class MemorySearchResult(BaseModel):
    memory: MemoryResponse
    score: float


class MemorySearchResponse(BaseModel):
    results: List[MemorySearchResult]
    total_found: int
    query_time_ms: int


class MemoryFilter(BaseModel):
    memory_type: Optional[str] = None
    project_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    key_pattern: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class MemoryStatsResponse(BaseModel):
    total_memories: int
    by_type: Dict[str, int]
    by_project: Dict[str, int]
    with_embeddings: int
    expired_count: int
    avg_importance: float


class MemoryConsolidateRequest(BaseModel):
    project_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    max_age_days: int = 30
    min_importance: float = 0.5


class MemoryConsolidateResponse(BaseModel):
    memories_reviewed: int
    memories_archived: int
    memories_deleted: int
    memories_merged: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    vector_index_status: str