"""
Task Scheduler models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class TaskCreate(BaseModel):
    project_id: UUID
    parent_task_id: Optional[UUID] = None
    assigned_agent_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    task_type: str = Field(default="task")  # epic, feature, task, subtask, microtask, atomic
    priority: int = Field(default=0, ge=0, le=10)
    dependencies: List[UUID] = []
    required_skills: List[str] = []
    required_tools: List[str] = []
    selected_model: Optional[str] = None
    selected_provider: Optional[str] = None
    expected_output: Dict[str, Any] = {}
    acceptance_criteria: Dict[str, Any] = {}
    max_retries: int = Field(default=3, ge=0, le=10)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, queued, running, completed, failed, cancelled, blocked
    priority: Optional[int] = None
    assigned_agent_id: Optional[str] = None
    selected_model: Optional[str] = None
    selected_provider: Optional[str] = None
    expected_output: Optional[Dict[str, Any]] = None
    acceptance_criteria: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_task_id: Optional[UUID]
    assigned_agent_id: Optional[str]
    title: str
    description: Optional[str]
    task_type: str
    priority: int
    dependencies: List[UUID]
    required_skills: List[str]
    required_tools: List[str]
    selected_model: Optional[str]
    selected_provider: Optional[str]
    expected_output: Dict[str, Any]
    acceptance_criteria: Dict[str, Any]
    status: str
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    result: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    queued_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskTreeResponse(BaseModel):
    task: TaskResponse
    children: List['TaskTreeResponse'] = []


TaskTreeResponse.model_rebuild()


class DecomposeRequest(BaseModel):
    requirements: str
    max_depth: int = Field(default=7, ge=1, le=10)
    include_subtasks: bool = True


class DecomposeResponse(BaseModel):
    tasks: List[TaskResponse]
    total_created: int


class TaskFilter(BaseModel):
    project_id: Optional[UUID] = None
    assigned_agent_id: Optional[str] = None
    status: Optional[str] = None
    task_type: Optional[str] = None
    parent_task_id: Optional[UUID] = None
    limit: int = Field(default=100, le=1000)
    offset: int = 0


class QueueStatsResponse(BaseModel):
    total_queued: int
    by_priority: Dict[int, int]
    by_type: Dict[str, int]
    avg_wait_time_ms: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    queue_depth: int