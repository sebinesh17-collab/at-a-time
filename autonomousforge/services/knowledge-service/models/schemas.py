"""
Knowledge Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class KnowledgeChunkCreate(BaseModel):
    project_id: UUID
    file_id: Optional[UUID] = None
    content: str = Field(..., min_length=1)
    chunk_index: int = Field(..., ge=0)
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class KnowledgeChunkUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None


class KnowledgeChunkResponse(BaseModel):
    id: UUID
    project_id: UUID
    file_id: Optional[UUID]
    chunk_index: int
    content: str
    metadata: Dict[str, Any]
    has_embedding: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    project_id: UUID
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=10, ge=1, le=100)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    file_ids: Optional[List[UUID]] = None
    metadata_filter: Optional[Dict[str, Any]] = None


class KnowledgeSearchResult(BaseModel):
    chunk: KnowledgeChunkResponse
    score: float
    highlight: Optional[str] = None


class KnowledgeSearchResponse(BaseModel):
    results: List[KnowledgeSearchResult]
    total_found: int
    query_time_ms: int


class KnowledgeIngestRequest(BaseModel):
    project_id: UUID
    file_ids: Optional[List[UUID]] = None
    chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=200, ge=0, le=2000)
    generate_embeddings: bool = True
    embedding_model: Optional[str] = None


class KnowledgeIngestResponse(BaseModel):
    project_id: UUID
    files_processed: int
    chunks_created: int
    embeddings_generated: int
    errors: List[Dict[str, str]]


class KnowledgeFilter(BaseModel):
    project_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    has_embedding: Optional[bool] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class KnowledgeStatsResponse(BaseModel):
    total_chunks: int
    chunks_with_embeddings: int
    projects_with_knowledge: int
    total_content_chars: int
    avg_chunk_size: int
    embedding_model: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    vector_index_status: str
    embedding_model: Optional[str] = None