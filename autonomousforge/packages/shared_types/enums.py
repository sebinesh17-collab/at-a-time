"""
Enums for AUTONOMOUSFORGE
"""
from enum import Enum


class AgentLevel(int, Enum):
    MASTER = 0
    PRINCIPAL = 1
    HEAD = 2
    TEAM_LEADER = 3
    WORKER = 4


class AgentStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    OFFLINE = "offline"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskType(str, Enum):
    EPIC = "epic"
    FEATURE = "feature"
    TASK = "task"
    SUBTASK = "subtask"
    MICROTASK = "microtask"
    ATOMIC = "atomic"


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_ACCEPTANCE = "task_acceptance"
    PROGRESS_UPDATE = "progress_update"
    COMPLETION = "completion"
    ERROR_REPORT = "error_report"
    REVIEW_REQUEST = "review_request"
    INTEGRATION_REQUEST = "integration_request"
    APPROVAL_REQUEST = "approval_request"
    ESCALATION = "escalation"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    MOBILE_ANDROID = "mobile-android"
    MOBILE_IOS = "mobile-ios"
    MOBILE_CROSS = "mobile-cross"
    WEB = "web"
    BACKEND = "backend"
    API = "api"
    DATABASE = "database"
    AI = "ai"
    AUTOMATION = "automation"
    FULLSTACK = "fullstack"


class ConversationMode(str, Enum):
    CHAT = "chat"
    CHAT_FILES = "chat_files"
    CHAT_FILES_SKILLS = "chat_files_skills"


class ApiKeyHealth(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"