"""
File Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class FileCreate(BaseModel):
    project_id: Optional[UUID] = None
    filename: str = Field(..., min_length=1, max_length=500)
    original_filename: str = Field(..., min_length=1, max_length=500)
    mime_type: str = Field(..., min_length=1, max_length=100)
    size_bytes: int = Field(..., ge=0)
    storage_path: str
    storage_provider: str = Field(default="local")  # local, s3, r2
    checksum_sha256: Optional[str] = None
    metadata: Dict[str, Any] = {}


class FileUpdate(BaseModel):
    filename: Optional[str] = Field(None, min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    is_processed: Optional[bool] = None
    processing_status: Optional[str] = None  # pending, processing, completed, failed
    processing_error: Optional[str] = None
    extracted_content: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None


class FileResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID]
    owner_id: UUID
    filename: str
    original_filename: str
    mime_type: str
    size_bytes: int
    storage_path: str
    storage_provider: str
    checksum_sha256: Optional[str]
    metadata: Dict[str, Any]
    extracted_content: Optional[str]
    analysis_result: Optional[Dict[str, Any]]
    is_processed: bool
    processing_status: str
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    file: FileResponse
    upload_url: Optional[str] = None  # For direct upload to S3/R2


class FileProcessRequest(BaseModel):
    file_id: UUID
    operations: List[str] = []  # extract_text, analyze_code, generate_embeddings, scan_security


class FileProcessResponse(BaseModel):
    file_id: UUID
    status: str
    operations_completed: List[str]
    operations_failed: List[Dict[str, str]]


class FileFilter(BaseModel):
    project_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    mime_type: Optional[str] = None
    is_processed: Optional[bool] = None
    processing_status: Optional[str] = None
    storage_provider: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class FileStatsResponse(BaseModel):
    total_files: int
    total_size_bytes: int
    by_mime_type: Dict[str, int]
    by_storage_provider: Dict[str, int]
    processed_count: int
    pending_count: int
    failed_count: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    storage_available_bytes: int
    storage_used_bytes: int