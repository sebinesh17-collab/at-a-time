"""
Master Orchestrator models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: str  # web, mobile-android, mobile-ios, mobile-cross, backend, api, database, ai, automation, fullstack
    tech_stack: List[str] = []
    repository_url: Optional[str] = None
    branch_name: str = "main"
    deployment_url: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    status: Optional[str] = None  # planning, active, building, testing, deployed, archived
    repository_url: Optional[str] = None
    branch_name: Optional[str] = None
    deployment_url: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    project_type: str
    tech_stack: List[str]
    status: str
    repository_url: Optional[str]
    branch_name: str
    deployment_url: Optional[str]
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    project_id: UUID
    title: str
    mode: str = "chat"  # chat, chat_files, chat_files_skills


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    owner_id: UUID
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    conversation_id: UUID
    role: str  # user, assistant, system
    content: str
    metadata: Dict[str, Any] = {}


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AgentMessageCreate(BaseModel):
    project_id: UUID
    task_id: Optional[UUID] = None
    sender_id: str
    recipient_id: str
    message_type: str  # task_assignment, task_acceptance, progress_update, completion, error_report, review_request, integration_request, approval_request, escalation
    content: Dict[str, Any]


class AgentMessageResponse(BaseModel):
    id: UUID
    project_id: UUID
    task_id: Optional[UUID]
    sender_id: str
    recipient_id: str
    message_type: str
    content: Dict[str, Any]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DecomposeRequest(BaseModel):
    requirements: str
    max_depth: int = 7


class SystemStatsResponse(BaseModel):
    total_projects: int
    active_projects: int
    total_tasks: int
    tasks_by_status: Dict[str, int]
    total_agents: int
    agents_by_level: Dict[str, int]
    agents_by_status: Dict[str, int]
    total_conversations: int
    total_messages: int


class ModelCallRequest(BaseModel):
    model: str
    prompt: str
    context: Dict[str, Any] = {}
    tools: List[Dict[str, Any]] = []


class ModelCallResponse(BaseModel):
    response: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    orchestrator_ready: bool