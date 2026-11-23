"""
Security utilities: password hashing, JWT, rate limiting
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt, JWTError
from passlib.context import CryptContext
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import redis.asyncio as redis
from .config import settings


# Password hashing with Argon2id
ph = PasswordHasher(
    time_cost=settings.argon2_time_cost,
    memory_cost=settings.argon2_memory_cost,
    parallelism=settings.argon2_parallelism,
    hash_len=32,
    salt_len=16
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id"""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against Argon2id hash"""
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def hash_master_key(key: str) -> str:
    """Hash master API key using SHA-256"""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_master_key(key: str, key_hash: str) -> bool:
    """Verify master API key against hash"""
    return secrets.compare_digest(hashlib.sha256(key.encode()).hexdigest(), key_hash)


def generate_master_key() -> str:
    """Generate a secure master API key"""
    return f"af_master_{secrets.token_urlsafe(32)}"


def generate_api_key_prefix(key: str, length: int = 8) -> str:
    """Generate prefix for API key identification"""
    return key[:length]


# JWT handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expiry_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[dict]:
    """Decode access token specifically"""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode refresh token specifically"""
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


# Rate limiting with Redis
class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window
        Returns: (allowed, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds

        # Remove old entries
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Count current requests
        current = await self.redis.zcard(key)

        if current >= limit:
            # Get oldest entry to calculate reset time
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1] + window_seconds)
            else:
                reset_time = int(now + window_seconds)
            return False, 0, reset_time

        # Add current request
        await self.redis.zadd(key, {f"{now}": now})
        await self.redis.expire(key, window_seconds + 1)

        remaining = limit - current - 1
        reset_time = int(now + window_seconds)
        return True, remaining, reset_time

    async def get_login_attempts(self, identifier: str) -> int:
        """Get current login attempts for identifier"""
        key = f"login_attempts:{identifier}"
        return await self.redis.zcard(key)

    async def record_login_attempt(self, identifier: str, success: bool):
        """Record login attempt"""
        key = f"login_attempts:{identifier}"
        now = time.time()
        window = settings.login_rate_window_minutes * 60

        if success:
            # Clear attempts on successful login
            await self.redis.delete(key)
        else:
            await self.redis.zadd(key, {f"{now}": now})
            await self.redis.expire(key, window + 1)

    async def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked due to too many failed attempts"""
        attempts = await self.get_login_attempts(identifier)
        return attempts >= settings.login_rate_limit


# Token hashing for storage
def hash_token(token: str) -> str:
    """Hash token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


# Secure random generation
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def generate_session_id() -> str:
    """Generate session ID"""
    return secrets.token_hex(16)