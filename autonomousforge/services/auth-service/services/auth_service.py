"""
Core authentication service
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
import secrets

from ..database import db
from ..utils.security import (
    hash_password, verify_password, hash_master_key, verify_master_key,
    generate_master_key, generate_api_key_prefix, hash_token,
    create_access_token, create_refresh_token, decode_access_token,
    decode_refresh_token, RateLimiter
)
from ..models.schemas import (
    OwnerSetupRequest, OwnerSetupResponse, OwnerInfo,
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    ChangePasswordRequest, SessionInfo, MasterKeyInfo,
    RegenerateMasterKeyResponse, ApiKeyCreateRequest, ApiKeyUpdateRequest,
    ApiKeyResponse, ApiKeyWithSecretResponse, TwoFASetupResponse,
    TwoFAVerifyRequest, TwoFADisableRequest, AuditLogResponse
)
from ..config import settings
import redis.asyncio as redis


class AuthService:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.rate_limiter: Optional[RateLimiter] = None

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.rate_limiter = RateLimiter(self.redis_client)

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    # ==================== Owner Setup ====================

    async def check_setup_complete(self) -> bool:
        """Check if owner setup is complete"""
        row = await db.fetchrow("SELECT is_setup_complete FROM owner LIMIT 1")
        return row and row["is_setup_complete"]

    async def setup_owner(self, request: OwnerSetupRequest) -> OwnerSetupResponse:
        """First-time owner setup"""
        # Check if already setup
        if await self.check_setup_complete():
            raise ValueError("Owner setup already complete")

        # Generate master API key if not provided
        master_key = request.master_api_key or generate_master_key()
        master_key_hash = hash_master_key(master_key)

        # Hash password
        password_hash = hash_password(request.password)

        # Create owner
        owner_id = uuid4()
        await db.execute("""
            INSERT INTO owner (id, email, display_name, password_hash, master_api_key_hash, is_setup_complete)
            VALUES ($1, $2, $3, $4, $5, TRUE)
        """, owner_id, request.email, request.display_name, password_hash, master_key_hash)

        # Log audit
        await self._log_audit("owner", str(owner_id), "owner_setup", "owner", str(owner_id),
                             {"email": request.email, "display_name": request.display_name})

        return OwnerSetupResponse(
            owner_id=owner_id,
            email=request.email,
            display_name=request.display_name,
            master_api_key=master_key,
            message="Owner account created successfully. Save your master API key - it will not be shown again!"
        )

    # ==================== Authentication ====================

    async def authenticate_owner(self, email: str, password: str, ip: str) -> Tuple[Optional[dict], str]:
        """Authenticate owner with email and password"""
        # Check rate limit
        blocked = await self.rate_limiter.is_blocked(ip)
        if blocked:
            raise ValueError("Too many login attempts. Please try again later.")

        # Get owner
        owner = await db.fetchrow("SELECT * FROM owner WHERE email = $1", email)
        if not owner:
            await self.rate_limiter.record_login_attempt(ip, False)
            raise ValueError("Invalid credentials")

        # Verify password
        if not verify_password(password, owner["password_hash"]):
            await self.rate_limiter.record_login_attempt(ip, False)
            await self._log_audit("owner", str(owner["id"]), "login_failed", "owner", str(owner["id"]),
                                 {"email": email, "reason": "invalid_password"}, ip)
            raise ValueError("Invalid credentials")

        # Success
        await self.rate_limiter.record_login_attempt(ip, True)
        return owner, "success"

    async def create_session(self, owner_id: UUID, ip: str, user_agent: str, remember_me: bool) -> Tuple[str, str]:
        """Create new session with access and refresh tokens"""
        # Create tokens
        access_token = create_access_token({"sub": str(owner_id), "session_id": generate_session_id()})
        refresh_token = create_refresh_token({"sub": str(owner_id)})

        # Hash tokens for storage
        access_hash = hash_token(access_token)
        refresh_hash = hash_token(refresh_token)

        # Calculate expiry
        access_expires = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
        refresh_expires = datetime.utcnow() + timedelta(days=settings.refresh_token_expiry_days)

        # Store session
        await db.execute("""
            INSERT INTO sessions (owner_id, token_hash, refresh_token_hash, expires_at, refresh_expires_at, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, owner_id, access_hash, refresh_hash, access_expires, refresh_expires, ip, user_agent)

        # Log audit
        await self._log_audit("owner", str(owner_id), "login", "session", None,
                             {"ip": ip, "user_agent": user_agent, "remember_me": remember_me}, ip)

        return access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        payload = decode_refresh_token(refresh_token)
        if not payload:
            return None

        owner_id = payload.get("sub")
        if not owner_id:
            return None

        # Verify refresh token exists and is valid
        refresh_hash = hash_token(refresh_token)
        session = await db.fetchrow("""
            SELECT * FROM sessions
            WHERE owner_id = $1 AND refresh_token_hash = $2 AND revoked_at IS NULL
            AND refresh_expires_at > NOW()
        """, UUID(owner_id), refresh_hash)

        if not session:
            return None

        # Create new access token
        new_access_token = create_access_token({"sub": owner_id, "session_id": generate_session_id()})
        new_access_hash = hash_token(new_access_token)
        new_expires = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)

        # Update session with new access token
        await db.execute("""
            UPDATE sessions SET token_hash = $1, expires_at = $2 WHERE id = $3
        """, new_access_hash, new_expires, session["id"])

        return new_access_token

    async def revoke_session(self, owner_id: UUID, token: str) -> bool:
        """Revoke a specific session"""
        token_hash = hash_token(token)
        result = await db.execute("""
            UPDATE sessions SET revoked_at = NOW()
            WHERE owner_id = $1 AND token_hash = $2 AND revoked_at IS NULL
        """, owner_id, token_hash)
        return result != "UPDATE 0"

    async def revoke_all_sessions(self, owner_id: UUID, except_token: Optional[str] = None) -> int:
        """Revoke all sessions for owner"""
        if except_token:
            except_hash = hash_token(except_token)
            result = await db.execute("""
                UPDATE sessions SET revoked_at = NOW()
                WHERE owner_id = $1 AND token_hash != $2 AND revoked_at IS NULL
            """, owner_id, except_hash)
        else:
            result = await db.execute("""
                UPDATE sessions SET revoked_at = NOW()
                WHERE owner_id = $1 AND revoked_at IS NULL
            """, owner_id)
        return int(result.split()[-1]) if result else 0

    async def get_sessions(self, owner_id: UUID, current_token: str) -> List[SessionInfo]:
        """Get all active sessions for owner"""
        current_hash = hash_token(current_token)
        rows = await db.fetch("""
            SELECT * FROM sessions
            WHERE owner_id = $1 AND revoked_at IS NULL AND expires_at > NOW()
            ORDER BY created_at DESC
        """, owner_id)

        sessions = []
        for row in rows:
            sessions.append(SessionInfo(
                id=row["id"],
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                is_current=row["token_hash"] == current_hash
            ))
        return sessions

    # ==================== Password Management ====================

    async def change_password(self, owner_id: UUID, current_password: str, new_password: str) -> bool:
        """Change owner password"""
        owner = await db.fetchrow("SELECT password_hash FROM owner WHERE id = $1", owner_id)
        if not owner:
            return False

        if not verify_password(current_password, owner["password_hash"]):
            raise ValueError("Current password is incorrect")

        new_hash = hash_password(new_password)
        await db.execute("UPDATE owner SET password_hash = $1, updated_at = NOW() WHERE id = $2", new_hash, owner_id)

        # Revoke all sessions except current (will be handled by caller)
        await self.revoke_all_sessions(owner_id)

        await self._log_audit("owner", str(owner_id), "password_change", "owner", str(owner_id))
        return True

    # ==================== Master API Key ====================

    async def get_master_key_info(self, owner_id: UUID) -> MasterKeyInfo:
        """Get master API key info (without the key itself)"""
        owner = await db.fetchrow("SELECT master_api_key_hash, created_at FROM owner WHERE id = $1", owner_id)
        if not owner:
            raise ValueError("Owner not found")

        # Get last used from audit logs
        last_used = await db.fetchrow("""
            SELECT timestamp FROM audit_logs
            WHERE actor_type = 'owner' AND actor_id = $1 AND action = 'master_key_used'
            ORDER BY timestamp DESC LIMIT 1
        """, str(owner_id))

        return MasterKeyInfo(
            key_prefix="af_master_********",
            created_at=owner["created_at"],
            last_used_at=last_used["timestamp"] if last_used else None,
            is_active=True
        )

    async def regenerate_master_key(self, owner_id: UUID, password: str) -> RegenerateMasterKeyResponse:
        """Regenerate master API key"""
        owner = await db.fetchrow("SELECT password_hash FROM owner WHERE id = $1", owner_id)
        if not owner:
            raise ValueError("Owner not found")

        if not verify_password(password, owner["password_hash"]):
            raise ValueError("Invalid password")

        new_key = generate_master_key()
        new_hash = hash_master_key(new_key)

        await db.execute("UPDATE owner SET master_api_key_hash = $1, updated_at = NOW() WHERE id = $2", new_hash, owner_id)

        await self._log_audit("owner", str(owner_id), "master_key_regenerated", "owner", str(owner_id))

        return RegenerateMasterKeyResponse(
            master_api_key=new_key,
            message="Master API key regenerated. Save it now - it will not be shown again!"
        )

    async def verify_master_key(self, key: str) -> Optional[UUID]:
        """Verify master API key and return owner_id"""
        owner = await db.fetchrow("SELECT id, master_api_key_hash FROM owner LIMIT 1")
        if not owner:
            return None

        if verify_master_key(key, owner["master_api_key_hash"]):
            await self._log_audit("owner", str(owner["id"]), "master_key_used", "owner", str(owner["id"]))
            return owner["id"]
        return None

    # ==================== API Key Management ====================

    async def create_api_key(self, owner_id: UUID, request: ApiKeyCreateRequest) -> ApiKeyWithSecretResponse:
        """Create new API key"""
        from ..utils.security import hash_token

        key_hash = hash_token(request.api_key)
        key_prefix = generate_api_key_prefix(request.api_key)

        key_id = uuid4()
        await db.execute("""
            INSERT INTO api_keys (id, provider, key_label, key_hash, key_prefix, expires_at, quota_limit, concurrency_limit, weight, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, key_id, request.provider, request.key_label, key_hash, key_prefix,
            request.expires_at, request.quota_limit, request.concurrency_limit, request.weight, request.metadata)

        await self._log_audit("owner", str(owner_id), "api_key_created", "api_key", str(key_id),
                             {"provider": request.provider, "label": request.key_label})

        return ApiKeyWithSecretResponse(
            id=key_id,
            provider=request.provider,
            key_label=request.key_label,
            key_prefix=key_prefix,
            is_enabled=True,
            expires_at=request.expires_at,
            last_used_at=None,
            usage_count=0,
            quota_limit=request.quota_limit,
            quota_used=0,
            health_status="unknown",
            failure_count=0,
            concurrency_limit=request.concurrency_limit,
            weight=request.weight,
            metadata=request.metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            api_key=request.api_key
        )

    async def list_api_keys(self, owner_id: UUID) -> List[ApiKeyResponse]:
        """List all API keys"""
        rows = await db.fetch("SELECT * FROM api_keys ORDER BY created_at DESC")
        return [ApiKeyResponse(**dict(row)) for row in rows]

    async def get_api_key(self, owner_id: UUID, key_id: UUID) -> Optional[ApiKeyResponse]:
        """Get API key by ID"""
        row = await db.fetchrow("SELECT * FROM api_keys WHERE id = $1", key_id)
        return ApiKeyResponse(**dict(row)) if row else None

    async def update_api_key(self, owner_id: UUID, key_id: UUID, request: ApiKeyUpdateRequest) -> Optional[ApiKeyResponse]:
        """Update API key"""
        updates = []
        params = []
        param_idx = 1

        for field, value in request.model_dump(exclude_unset=True).items():
            if field == "metadata":
                updates.append(f"metadata = metadata || ${param_idx}")
            else:
                updates.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1

        if not updates:
            return await self.get_api_key(owner_id, key_id)

        params.append(key_id)
        query = f"UPDATE api_keys SET {', '.join(updates)}, updated_at = NOW() WHERE id = ${param_idx}"
        await db.execute(query, *params)

        await self._log_audit("owner", str(owner_id), "api_key_updated", "api_key", str(key_id),
                             request.model_dump(exclude_unset=True))

        return await self.get_api_key(owner_id, key_id)

    async def delete_api_key(self, owner_id: UUID, key_id: UUID) -> bool:
        """Delete API key"""
        result = await db.execute("DELETE FROM api_keys WHERE id = $1", key_id)
        if result != "DELETE 0":
            await self._log_audit("owner", str(owner_id), "api_key_deleted", "api_key", str(key_id))
            return True
        return False

    async def verify_api_key(self, key: str) -> Optional[dict]:
        """Verify API key and return key info"""
        key_hash = hash_token(key)
        row = await db.fetchrow("""
            SELECT * FROM api_keys WHERE key_hash = $1 AND is_enabled = TRUE
            AND (expires_at IS NULL OR expires_at > NOW())
        """, key_hash)

        if row:
            # Update usage
            await db.execute("""
                UPDATE api_keys SET last_used_at = NOW(), usage_count = usage_count + 1
                WHERE id = $1
            """, row["id"])
            return dict(row)
        return None

    # ==================== 2FA ====================

    async def setup_2fa(self, owner_id: UUID) -> TwoFASetupResponse:
        """Setup 2FA for owner"""
        import pyotp
        import qrcode
        import io
        import base64

        owner = await db.fetchrow("SELECT email FROM owner WHERE id = $1", owner_id)
        if not owner:
            raise ValueError("Owner not found")

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(owner["email"], issuer_name="AUTONOMOUSFORGE")

        # Generate QR code
        qr = qrcode.make(uri)
        buffered = io.BytesIO()
        qr.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # Store secret (encrypted in production)
        await db.execute("UPDATE owner SET two_fa_secret = $1 WHERE id = $2", secret, owner_id)

        return TwoFASetupResponse(
            secret=secret,
            qr_code=qr_base64,
            backup_codes=backup_codes
        )

    async def verify_2fa(self, owner_id: UUID, code: str) -> bool:
        """Verify 2FA code"""
        import pyotp

        owner = await db.fetchrow("SELECT two_fa_secret FROM owner WHERE id = $1", owner_id)
        if not owner or not owner["two_fa_secret"]:
            return False

        totp = pyotp.TOTP(owner["two_fa_secret"])
        return totp.verify(code, valid_window=1)

    async def disable_2fa(self, owner_id: UUID, password: str, code: str) -> bool:
        """Disable 2FA"""
        owner = await db.fetchrow("SELECT password_hash, two_fa_secret FROM owner WHERE id = $1", owner_id)
        if not owner:
            return False

        if not verify_password(password, owner["password_hash"]):
            raise ValueError("Invalid password")

        if not await self.verify_2fa(owner_id, code):
            raise ValueError("Invalid 2FA code")

        await db.execute("UPDATE owner SET two_fa_secret = NULL WHERE id = $1", owner_id)
        await self._log_audit("owner", str(owner_id), "2fa_disabled", "owner", str(owner_id))
        return True

    # ==================== Audit Logs ====================

    async def _log_audit(self, actor_type: str, actor_id: str, action: str,
                         resource_type: Optional[str] = None, resource_id: Optional[str] = None,
                         details: dict = None, ip: str = None, success: bool = True, error: str = None):
        """Log audit event"""
        await db.execute("""
            INSERT INTO audit_logs (actor_type, actor_id, action, resource_type, resource_id, details, ip_address, success, error_message)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, actor_type, actor_id, action, resource_type, resource_id, details or {}, ip, success, error)

    async def get_audit_logs(self, owner_id: UUID, limit: int = 100, offset: int = 0) -> List[AuditLogResponse]:
        """Get audit logs for owner"""
        rows = await db.fetch("""
            SELECT * FROM audit_logs
            WHERE actor_type = 'owner' AND actor_id = $1
            ORDER BY timestamp DESC
            LIMIT $2 OFFSET $3
        """, str(owner_id), limit, offset)
        return [AuditLogResponse(**dict(row)) for row in rows]

    # ==================== Token Validation ====================

    async def validate_access_token(self, token: str) -> Optional[UUID]:
        """Validate access token and return owner_id"""
        payload = decode_access_token(token)
        if not payload:
            return None

        owner_id = payload.get("sub")
        session_id = payload.get("session_id")
        if not owner_id or not session_id:
            return None

        token_hash = hash_token(token)
        session = await db.fetchrow("""
            SELECT owner_id FROM sessions
            WHERE owner_id = $1 AND token_hash = $2 AND revoked_at IS NULL AND expires_at > NOW()
        """, UUID(owner_id), token_hash)

        return UUID(session["owner_id"]) if session else None


# Global auth service instance
auth_service = AuthService()