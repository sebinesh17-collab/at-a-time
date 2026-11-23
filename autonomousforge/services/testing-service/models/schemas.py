"""
Testing Service models and schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class TestSuiteCreate(BaseModel):
    project_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    test_type: str = Field(..., pattern=r'^(unit|integration|e2e|performance|security|load)$')
    configuration: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    schedule: Optional[str] = None  # cron expression


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, str]] = None
    schedule: Optional[str] = None
    is_enabled: Optional[bool] = None


class TestSuiteResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    test_type: str
    configuration: Dict[str, Any]
    environment: Dict[str, str]
    schedule: Optional[str]
    is_enabled: bool
    last_run_at: Optional[datetime]
    last_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseCreate(BaseModel):
    suite_id: UUID
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    test_code: str
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    retries: int = Field(default=0, ge=0, le=5)
    is_flaky: bool = False


class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_code: Optional[str] = None
    dependencies: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    timeout_seconds: Optional[int] = None
    retries: Optional[int] = None
    is_flaky: Optional[bool] = None


class TestCaseResponse(BaseModel):
    id: UUID
    suite_id: UUID
    name: str
    description: Optional[str]
    test_code: str
    dependencies: List[str]
    tags: List[str]
    timeout_seconds: int
    retries: int
    is_flaky: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestRunCreate(BaseModel):
    suite_id: UUID
    trigger_type: str = Field(default="manual")  # manual, scheduled, push, pr, api
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    selected_cases: Optional[List[UUID]] = None


class TestRunUpdate(BaseModel):
    status: Optional[str] = None  # queued, running, completed, failed, cancelled
    current_case: Optional[str] = None
    progress: Optional[int] = None


class TestRunResponse(BaseModel):
    id: UUID
    suite_id: UUID
    trigger_type: str
    trigger_data: Dict[str, Any]
    environment: Dict[str, str]
    status: str
    current_case: Optional[str]
    progress: int
    total_cases: int
    passed: int
    failed: int
    skipped: int
    errored: int
    duration_ms: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    queued_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestResultCreate(BaseModel):
    run_id: UUID
    case_id: UUID
    status: str = Field(..., pattern=r'^(passed|failed|skipped|errored)$')
    duration_ms: int
    output: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    assertions: List[Dict[str, Any]] = Field(default_factory=list)
    coverage: Optional[Dict[str, Any]] = None


class TestResultResponse(BaseModel):
    id: UUID
    run_id: UUID
    case_id: UUID
    status: str
    duration_ms: int
    output: Optional[str]
    error_message: Optional[str]
    stack_trace: Optional[str]
    assertions: List[Dict[str, Any]]
    coverage: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class TestSuiteFilter(BaseModel):
    project_id: Optional[UUID] = None
    test_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class TestRunFilter(BaseModel):
    suite_id: Optional[UUID] = None
    status: Optional[str] = None
    trigger_type: Optional[str] = None
    limit: int = Field(default=50, le=500)
    offset: int = 0


class TestStatsResponse(BaseModel):
    total_suites: int
    total_cases: int
    total_runs: int
    runs_by_status: Dict[str, int]
    avg_duration_ms: int
    pass_rate: float
    flaky_cases: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    queue_depth: int
    active_runs: int