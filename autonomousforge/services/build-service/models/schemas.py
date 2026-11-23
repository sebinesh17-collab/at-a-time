"""
Build Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class BuildCreate(BaseModel):
    project_id: UUID
    trigger_type: str = Field(default="manual")  # manual, push, pr, scheduled, webhook
    trigger_data: Dict[str, Any] = {}
    branch_name: str = "main"
    commit_sha: Optional[str] = None
    build_config: Dict[str, Any] = {}


class BuildUpdate(BaseModel):
    status: Optional[str] = None  # queued, running, completed, failed, cancelled
    current_stage: Optional[str] = None
    progress: Optional[int] = None
    logs: Optional[str] = None
    artifacts: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None


class BuildResponse(BaseModel):
    id: UUID
    project_id: UUID
    trigger_type: str
    trigger_data: Dict[str, Any]
    branch_name: str
    commit_sha: Optional[str]
    build_config: Dict[str, Any]
    status: str
    current_stage: Optional[str]
    progress: int
    logs: Optional[str]
    artifacts: List[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    queued_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuildStageCreate(BaseModel):
    build_id: UUID
    name: str
    order: int
    commands: List[str] = []
    environment: Dict[str, str] = {}
    timeout_seconds: int = 300


class BuildStageResponse(BaseModel):
    id: UUID
    build_id: UUID
    name: str
    order: int
    commands: List[str]
    environment: Dict[str, str]
    timeout_seconds: int
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    logs: Optional[str]
    exit_code: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BuildLogCreate(BaseModel):
    build_id: UUID
    stage_id: Optional[UUID] = None
    level: str = "info"  # debug, info, warn, error
    message: str
    source: str = "build"


class BuildLogResponse(BaseModel):
    id: UUID
    build_id: UUID
    stage_id: Optional[UUID]
    level: str
    message: str
    source: str
    timestamp: datetime

    class Config:
        from_attributes = True


class BuildFilter(BaseModel):
    project_id: Optional[UUID] = None
    status: Optional[str] = None
    trigger_type: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class BuildStatsResponse(BaseModel):
    total_builds: int
    builds_by_status: Dict[str, int]
    avg_duration_seconds: float
    success_rate: float


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    queue_depth: int