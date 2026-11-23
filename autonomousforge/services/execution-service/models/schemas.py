"""
Execution Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ExecutionCreate(BaseModel):
    project_id: UUID
    task_id: Optional[UUID] = None
    command: str
    working_directory: Optional[str] = None
    environment: Dict[str, str] = {}
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    docker_image: Optional[str] = None
    docker_config: Dict[str, Any] = {}


class ExecutionUpdate(BaseModel):
    status: Optional[str] = None  # queued, running, completed, failed, cancelled, timeout
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error_message: Optional[str] = None


class ExecutionResponse(BaseModel):
    id: UUID
    project_id: UUID
    task_id: Optional[UUID]
    command: str
    working_directory: Optional[str]
    environment: Dict[str, str]
    timeout_seconds: int
    docker_image: Optional[str]
    docker_config: Dict[str, Any]
    status: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    queued_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SandboxCreate(BaseModel):
    project_id: UUID
    name: str = Field(..., min_length=1, max_length=100)
    base_image: str = "python:3.11-slim"
    environment: Dict[str, str] = {}
    ports: List[int] = []
    volumes: List[Dict[str, str]] = []
    resources: Dict[str, Any] = {}
    auto_destroy_seconds: int = Field(default=3600, ge=60, le=86400)


class SandboxUpdate(BaseModel):
    status: Optional[str] = None  # creating, running, stopped, destroyed
    container_id: Optional[str] = None
    endpoint: Optional[str] = None


class SandboxResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    base_image: str
    environment: Dict[str, str]
    ports: List[int]
    volumes: List[Dict[str, str]]
    resources: Dict[str, Any]
    auto_destroy_seconds: int
    status: str
    container_id: Optional[str]
    endpoint: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SandboxCommand(BaseModel):
    command: str
    working_directory: Optional[str] = None
    environment: Dict[str, str] = {}
    timeout_seconds: int = Field(default=60, ge=1, le=300)


class SandboxCommandResponse(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int


class ExecutionFilter(BaseModel):
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class SandboxFilter(BaseModel):
    project_id: Optional[UUID] = None
    status: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class ExecutionStatsResponse(BaseModel):
    total_executions: int
    executions_by_status: Dict[str, int]
    avg_duration_seconds: float
    success_rate: float
    active_sandboxes: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    active_containers: int