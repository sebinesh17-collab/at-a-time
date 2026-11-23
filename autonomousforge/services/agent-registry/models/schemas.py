"""
Agent Registry models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AgentCreate(BaseModel):
    id: str = Field(..., pattern=r'^(M-\d{3}|P-\d{2}|H-\d{3}|TL-\d{4}|W-\d{5})$')
    name: str
    role: str  # Master Agent, Principal Agent, Head Agent, Team Leader Agent, Worker Agent
    department: str
    level: int = Field(..., ge=0, le=4)  # 0=master, 1=principal, 2=head, 3=team_leader, 4=worker
    parent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: str = "nemotron-3-ultra"
    provider: str = "nvidia"
    tools: List[str] = []
    skills: List[str] = []
    permissions: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    level: Optional[int] = Field(None, ge=0, le=4)
    parent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    tools: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    permissions: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    department: str
    level: int
    parent_id: Optional[str]
    system_prompt: Optional[str]
    model_id: str
    provider: str
    tools: List[str]
    skills: List[str]
    permissions: Dict[str, Any]
    status: str
    current_task_id: Optional[UUID]
    tasks_completed: int
    tasks_failed: int
    avg_execution_time_ms: int
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HierarchyResponse(BaseModel):
    master: Dict[str, int]
    principals: Dict[str, int]
    heads: Dict[str, int]
    team_leaders: Dict[str, int]
    workers: Dict[str, int]


class AgentStatusUpdate(BaseModel):
    agent_id: str
    status: str  # idle, active, paused, error, offline
    current_task_id: Optional[UUID] = None


class BulkAgentCreate(BaseModel):
    agents: List[AgentCreate]


class AgentFilter(BaseModel):
    level: Optional[int] = None
    department: Optional[str] = None
    status: Optional[str] = None
    parent_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


class StatsResponse(BaseModel):
    total_agents: int
    by_level: Dict[str, int]
    by_department: Dict[str, int]
    by_status: Dict[str, int]
    active_tasks: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    agents_loaded: int