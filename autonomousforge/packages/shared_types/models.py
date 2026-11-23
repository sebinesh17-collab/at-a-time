"""
Data models for AUTONOMOUSFORGE
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import json

from .enums import (
    AgentLevel, AgentStatus, TaskStatus, TaskType, MessageType,
    ProjectStatus, ProjectType, ConversationMode, ApiKeyHealth, WorkflowStatus
)


@dataclass
class Owner:
    id: UUID
    email: str
    display_name: str
    password_hash: str
    master_api_key_hash: str
    two_fa_secret: Optional[str] = None
    is_setup_complete: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Session:
    id: UUID
    owner_id: UUID
    token_hash: str
    refresh_token_hash: Optional[str] = None
    expires_at: datetime = field(default_factory=datetime.utcnow)
    refresh_expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.utcnow()


@dataclass
class ApiKey:
    id: UUID
    provider: str
    key_label: str
    key_hash: str
    key_prefix: str
    is_enabled: bool = True
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    quota_limit: Optional[int] = None
    quota_used: int = 0
    quota_reset_at: datetime = field(default_factory=datetime.utcnow)
    health_status: ApiKeyHealth = ApiKeyHealth.UNKNOWN
    failure_count: int = 0
    consecutive_failures: int = 0
    last_health_check: Optional[datetime] = None
    concurrency_limit: int = 10
    weight: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Agent:
    id: str  # M-001, P-01, H-001, TL-001, W-0001
    name: str
    role: str
    department: Optional[str] = None
    level: AgentLevel = AgentLevel.WORKER
    parent_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    provider: str = "nvidia"
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    permissions: Dict[str, Any] = field(default_factory=dict)
    memory_config: Dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: Optional[UUID] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_execution_time_ms: int = 0
    last_active_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Project:
    id: UUID
    name: str
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    tech_stack: List[str] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.PLANNING
    owner_id: UUID = field(default_factory=uuid4)
    repository_url: Optional[str] = None
    branch_name: str = "main"
    deployment_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Task:
    id: UUID
    project_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    assigned_agent_id: Optional[str] = None
    title: str = ""
    description: Optional[str] = None
    task_type: TaskType = TaskType.TASK
    priority: int = 0
    dependencies: List[UUID] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    selected_model: Optional[str] = None
    selected_provider: Optional[str] = None
    expected_output: Dict[str, Any] = field(default_factory=dict)
    acceptance_criteria: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    queued_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Message:
    id: UUID
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    sender_id: Optional[str] = None
    recipient_id: Optional[str] = None
    message_type: MessageType = MessageType.TASK_ASSIGNMENT
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: str = "sent"
    output_references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class File:
    id: UUID
    project_id: Optional[UUID] = None
    owner_id: UUID = field(default_factory=uuid4)
    filename: str = ""
    original_filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    storage_path: str = ""
    storage_provider: str = "local"
    checksum_sha256: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_content: Optional[str] = None
    analysis_result: Dict[str, Any] = field(default_factory=dict)
    is_processed: bool = False
    processing_status: str = "pending"
    processing_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    id: UUID
    project_id: Optional[UUID] = None
    owner_id: UUID = field(default_factory=uuid4)
    title: Optional[str] = None
    mode: ConversationMode = ConversationMode.CHAT
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChatMessage:
    id: UUID
    conversation_id: UUID
    role: str  # user, assistant, system, tool
    content: str = ""
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    model_used: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    latency_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    id: UUID
    actor_type: str  # owner, agent, system
    actor_id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeChunk:
    id: UUID
    project_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    chunk_index: int = 0
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Workflow:
    id: UUID
    project_id: Optional[UUID] = None
    name: str = ""
    description: Optional[str] = None
    definition: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    id: UUID
    workflow_id: UUID
    project_id: Optional[UUID] = None
    trigger_type: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.RUNNING
    current_node_id: Optional[str] = None
    execution_data: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class Skill:
    id: UUID
    name: str
    category: str
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    is_system: bool = False
    is_enabled: bool = True
    version: int = 1
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Tool:
    id: UUID
    name: str
    category: str
    description: Optional[str] = None
    schema: Dict[str, Any] = field(default_factory=dict)
    implementation_type: Optional[str] = None
    implementation_config: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    is_system: bool = False
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class McpServer:
    id: UUID
    name: str
    description: Optional[str] = None
    transport: str = "stdio"
    connection_config: Dict[str, Any] = field(default_factory=dict)
    auth_config: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    status: str = "disconnected"
    last_connected: Optional[datetime] = None
    error_message: Optional[str] = None
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Memory:
    id: UUID
    memory_type: str
    owner_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    key: str = ""
    value: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    importance: float = 1.0
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)