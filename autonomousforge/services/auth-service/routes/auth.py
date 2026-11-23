"""
Auth routes
"""
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from typing import Optional
import json

from ..services.auth_service import auth_service
from ..models.schemas import (
    OwnerSetupRequest, LoginRequest, RefreshRequest, ChangePasswordRequest,
    ApiKeyCreateRequest, ApiKeyUpdateRequest, TwoFAVerifyRequest, TwoFADisableRequest,
    ErrorResponse, ValidationErrorResponse
)
from ..utils.security import decode_access_token, hash_token
from ..config import settings


def require_auth(handler):
    """Decorator to require authentication"""
    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]
        owner_id = await auth_service.validate_access_token(token)
        if not owner_id:
            return json_response({"error": "unauthorized", "message": "Invalid or expired token"}, status=401)

        request["owner_id"] = owner_id
        request["access_token"] = token
        return await handler(request)
    return wrapper


def require_master_key(handler):
    """Decorator to require master API key"""
    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]
        # Check if it's master key format
        if token.startswith("af_master_"):
            owner_id = await auth_service.verify_master_key(token)
            if not owner_id:
                return json_response({"error": "unauthorized", "message": "Invalid master API key"}, status=401)
            request["owner_id"] = owner_id
            request["is_master_key"] = True
            return await handler(request)
        else:
            # Try regular token
            owner_id = await auth_service.validate_access_token(token)
            if not owner_id:
                return json_response({"error": "unauthorized", "message": "Invalid token"}, status=401)
            request["owner_id"] = owner_id
            request["is_master_key"] = False
            return await handler(request)
    return wrapper


# ==================== Setup ====================

async def setup_owner(request: Request):
    """First-time owner setup"""
    if await auth_service.check_setup_complete():
        return json_response({"error": "already_setup", "message": "Owner setup already complete"}, status=400)

    try:
        data = await request.json()
        setup_request = OwnerSetupRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await auth_service.setup_owner(setup_request)
        return json_response(result.model_dump(), status=201)
    except ValueError as e:
        return json_response({"error": "setup_error", "message": str(e)}, status=400)


async def check_setup(request: Request):
    """Check if setup is complete"""
    is_complete = await auth_service.check_setup_complete()
    return json_response({"setup_complete": is_complete})


# ==================== Authentication ====================

async def login(request: Request):
    """Owner login"""
    # Get client IP
    ip = request.headers.get("X-Forwarded-For", request.remote).split(",")[0].strip()

    try:
        data = await request.json()
        login_request = LoginRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        owner, _ = await auth_service.authenticate_owner(login_request.email, login_request.password, ip)
    except ValueError as e:
        return json_response({"error": "authentication_failed", "message": str(e)}, status=401)

    # Check 2FA
    owner_row = await auth_service.db.fetchrow("SELECT two_fa_secret FROM owner WHERE id = $1", owner["id"])
    if owner_row and owner_row["two_fa_secret"]:
        # 2FA required - return partial response
        return json_response({
            "requires_2fa": True,
            "message": "Two-factor authentication required",
            "temp_token": "2fa_required"  # In production, use a proper temp token
        }, status=200)

    # Create session
    user_agent = request.headers.get("User-Agent", "")
    access_token, refresh_token = await auth_service.create_session(
        owner["id"], ip, user_agent, login_request.remember_me
    )

    return json_response(LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiry_hours * 3600,
        owner=OwnerInfo(
            id=owner["id"],
            email=owner["email"],
            display_name=owner["display_name"],
            is_setup_complete=owner["is_setup_complete"],
            created_at=owner["created_at"]
        )
    ).model_dump())


async def login_2fa(request: Request):
    """Complete 2FA login"""
    ip = request.headers.get("X-Forwarded-For", request.remote).split(",")[0].strip()

    try:
        data = await request.json()
        verify_request = TwoFAVerifyRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    # Get owner from temp context (simplified - in production use proper temp token)
    # For now, require email in request
    email = data.get("email")
    if not email:
        return json_response({"error": "validation_error", "message": "Email required"}, status=400)

    owner = await auth_service.db.fetchrow("SELECT * FROM owner WHERE email = $1", email)
    if not owner:
        return json_response({"error": "not_found", "message": "Owner not found"}, status=404)

    if not await auth_service.verify_2fa(owner["id"], verify_request.code):
        return json_response({"error": "invalid_code", "message": "Invalid 2FA code"}, status=401)

    user_agent = request.headers.get("User-Agent", "")
    access_token, refresh_token = await auth_service.create_session(
        owner["id"], ip, user_agent, True
    )

    return json_response(LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_expiry_hours * 3600,
        owner=OwnerInfo(
            id=owner["id"],
            email=owner["email"],
            display_name=owner["display_name"],
            is_setup_complete=owner["is_setup_complete"],
            created_at=owner["created_at"]
        )
    ).model_dump())


async def logout(request: Request):
    """Logout - revoke current session"""
    owner_id = request["owner_id"]
    token = request["access_token"]
    await auth_service.revoke_session(owner_id, token)
    return json_response({"message": "Logged out successfully"})


async def logout_all(request: Request):
    """Logout from all sessions"""
    owner_id = request["owner_id"]
    current_token = request["access_token"]
    count = await auth_service.revoke_all_sessions(owner_id, current_token)
    return json_response({"message": f"Revoked {count} other sessions"})


async def refresh_token(request: Request):
    """Refresh access token"""
    try:
        data = await request.json()
        refresh_request = RefreshRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    new_token = await auth_service.refresh_access_token(refresh_request.refresh_token)
    if not new_token:
        return json_response({"error": "invalid_token", "message": "Invalid or expired refresh token"}, status=401)

    return json_response(RefreshResponse(
        access_token=new_token,
        expires_in=settings.jwt_expiry_hours * 3600
    ).model_dump())


async def get_me(request: Request):
    """Get current owner info"""
    owner_id = request["owner_id"]
    owner = await auth_service.db.fetchrow("SELECT id, email, display_name, is_setup_complete, created_at FROM owner WHERE id = $1", owner_id)
    if not owner:
        return json_response({"error": "not_found", "message": "Owner not found"}, status=404)

    return json_response(OwnerInfo(**dict(owner)).model_dump())


# ==================== Password ====================

async def change_password(request: Request):
    """Change password"""
    owner_id = request["owner_id"]

    try:
        data = await request.json()
        change_request = ChangePasswordRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        await auth_service.change_password(owner_id, change_request.current_password, change_request.new_password)
        return json_response({"message": "Password changed successfully. Please log in again."})
    except ValueError as e:
        return json_response({"error": "password_error", "message": str(e)}, status=400)


# ==================== Master API Key ====================

async def get_master_key_info(request: Request):
    """Get master key info"""
    owner_id = request["owner_id"]
    info = await auth_service.get_master_key_info(owner_id)
    return json_response(info.model_dump())


async def regenerate_master_key(request: Request):
    """Regenerate master API key"""
    owner_id = request["owner_id"]

    try:
        data = await request.json()
        password = data.get("password")
        if not password:
            return json_response({"error": "validation_error", "message": "Password required"}, status=400)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await auth_service.regenerate_master_key(owner_id, password)
        return json_response(result.model_dump())
    except ValueError as e:
        return json_response({"error": "regeneration_failed", "message": str(e)}, status=400)


# ==================== API Keys ====================

async def create_api_key(request: Request):
    """Create API key"""
    owner_id = request["owner_id"]

    try:
        data = await request.json()
        create_request = ApiKeyCreateRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await auth_service.create_api_key(owner_id, create_request)
        return json_response(result.model_dump(), status=201)
    except ValueError as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=400)


async def list_api_keys(request: Request):
    """List API keys"""
    owner_id = request["owner_id"]
    keys = await auth_service.list_api_keys(owner_id)
    return json_response([k.model_dump() for k in keys])


async def get_api_key(request: Request):
    """Get API key"""
    owner_id = request["owner_id"]
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    key = await auth_service.get_api_key(owner_id, key_uuid)
    if not key:
        return json_response({"error": "not_found", "message": "API key not found"}, status=404)

    return json_response(key.model_dump())


async def update_api_key(request: Request):
    """Update API key"""
    owner_id = request["owner_id"]
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    try:
        data = await request.json()
        update_request = ApiKeyUpdateRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    key = await auth_service.update_api_key(owner_id, key_uuid, update_request)
    if not key:
        return json_response({"error": "not_found", "message": "API key not found"}, status=404)

    return json_response(key.model_dump())


async def delete_api_key(request: Request):
    """Delete API key"""
    owner_id = request["owner_id"]
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    success = await auth_service.delete_api_key(owner_id, key_uuid)
    if not success:
        return json_response({"error": "not_found", "message": "API key not found"}, status=404)

    return json_response({"message": "API key deleted"})


# ==================== 2FA ====================

async def setup_2fa(request: Request):
    """Setup 2FA"""
    owner_id = request["owner_id"]
    result = await auth_service.setup_2fa(owner_id)
    return json_response(result.model_dump())


async def verify_2fa(request: Request):
    """Verify and enable 2FA"""
    owner_id = request["owner_id"]

    try:
        data = await request.json()
        verify_request = TwoFAVerifyRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    if await auth_service.verify_2fa(owner_id, verify_request.code):
        return json_response({"message": "2FA enabled successfully"})
    return json_response({"error": "invalid_code", "message": "Invalid 2FA code"}, status=400)


async def disable_2fa(request: Request):
    """Disable 2FA"""
    owner_id = request["owner_id"]

    try:
        data = await request.json()
        disable_request = TwoFADisableRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        await auth_service.disable_2fa(owner_id, disable_request.password, disable_request.code)
        return json_response({"message": "2FA disabled"})
    except ValueError as e:
        return json_response({"error": "disable_failed", "message": str(e)}, status=400)


# ==================== Sessions ====================

async def list_sessions(request: Request):
    """List active sessions"""
    owner_id = request["owner_id"]
    current_token = request["access_token"]
    sessions = await auth_service.get_sessions(owner_id, current_token)
    return json_response([s.model_dump() for s in sessions])


async def revoke_session(request: Request):
    """Revoke specific session"""
    owner_id = request["owner_id"]
    session_id = request.match_info.get("session_id")
    try:
        session_uuid = UUID(session_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid session ID"}, status=400)

    # Get session token hash
    session = await auth_service.db.fetchrow("SELECT token_hash FROM sessions WHERE id = $1 AND owner_id = $2", session_uuid, owner_id)
    if not session:
        return json_response({"error": "not_found", "message": "Session not found"}, status=404)

    # Can't revoke via token hash directly, need to find by ID
    await auth_service.db.execute("UPDATE sessions SET revoked_at = NOW() WHERE id = $1", session_uuid)
    return json_response({"message": "Session revoked"})


# ==================== Audit Logs ====================

async def get_audit_logs(request: Request):
    """Get audit logs"""
    owner_id = request["owner_id"]
    limit = int(request.query.get("limit", 100))
    offset = int(request.query.get("offset", 0))
    logs = await auth_service.get_audit_logs(owner_id, limit, offset)
    return json_response([log.model_dump() for log in logs])


# ==================== Health ====================

async def health_check(request: Request):
    """Health check endpoint"""
    # Check database
    try:
        await auth_service.db.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    # Check Redis
    try:
        await auth_service.redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"

    return json_response({
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "service": "auth-service",
        "version": "1.0.0",
        "database": db_status,
        "redis": redis_status
    })


# Import at bottom to avoid circular
from uuid import UUID
from ..database import db as auth_db
auth_service.db = auth_db