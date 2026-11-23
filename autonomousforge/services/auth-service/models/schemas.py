"""
Pydantic schemas for auth service
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Owner Setup
class OwnerSetupRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=12, max_length=128)
    master_api_key: Optional[str] = None  # If not provided, will be generated


class OwnerSetupResponse(BaseModel):
    owner_id: UUID
    email: str
    display_name: str
    master_api_key: str  # Only returned once!
    message: str


# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    owner: "OwnerInfo"


class OwnerInfo(BaseModel):
    id: UUID
    email: str
    display_name: str
    is_setup_complete: bool
    created_at: datetime


# Token Refresh
class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Password Change
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        # Check for at least one uppercase, lowercase, digit, special char
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)

        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        return v


# Session Info
class SessionInfo(BaseModel):
    id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool = False


# Master API Key
class MasterKeyInfo(BaseModel):
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool


class RegenerateMasterKeyResponse(BaseModel):
    master_api_key: str  # Only returned once!
    message: str


# API Key Management
class ApiKeyCreateRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    key_label: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=10)
    expires_at: Optional[datetime] = None
    quota_limit: Optional[int] = None
    concurrency_limit: int = 10
    weight: int = 100
    metadata: Dict[str, Any] = {}


class ApiKeyUpdateRequest(BaseModel):
    key_label: Optional[str] = Field(None, min_length=1, max_length=100)
    is_enabled: Optional[bool] = None
    expires_at: Optional[datetime] = None
    quota_limit: Optional[int] = None
    concurrency_limit: Optional[int] = None
    weight: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ApiKeyResponse(BaseModel):
    id: UUID
    provider: str
    key_label: str
    key_prefix: str
    is_enabled: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    quota_limit: Optional[int]
    quota_used: int
    health_status: str
    failure_count: int
    concurrency_limit: int
    weight: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ApiKeyWithSecretResponse(ApiKeyResponse):
    api_key: str  # Only returned on creation


# 2FA
class TwoFASetupResponse(BaseModel):
    secret: str
    qr_code: str  # Base64 encoded PNG
    backup_codes: List[str]


class TwoFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class TwoFADisableRequest(BaseModel):
    password: str
    code: str = Field(..., min_length=6, max_length=6)


# Audit Logs
class AuditLogResponse(BaseModel):
    id: UUID
    actor_type: str
    actor_id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    success: bool
    error_message: Optional[str]
    timestamp: datetime


# Error Responses
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    message: str
    errors: List[Dict[str, Any]]


# Health Check
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    redis: str


# Update forward references
OwnerSetupResponse.model_rebuild()
LoginResponse.model_rebuild()