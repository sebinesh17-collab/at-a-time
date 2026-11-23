"""
Authentication middleware for API Gateway
"""
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from typing import Optional, Callable, Awaitable
from jose import jwt, JWTError
import hashlib
import redis.asyncio as redis

from ..config import settings


class AuthMiddleware:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    async def validate_token(self, token: str) -> Optional[dict]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "access":
                return None

            # Check if session is still valid in Redis (for revoked sessions)
            session_id = payload.get("session_id")
            if session_id:
                revoked = await self.redis_client.get(f"revoked_session:{session_id}")
                if revoked:
                    return None

            return payload
        except JWTError:
            return None

    async def verify_master_key(self, key: str) -> Optional[str]:
        """Verify master API key"""
        if not settings.master_api_key:
            return None
        if key == settings.master_api_key:
            return "master"
        return None

    @web.middleware
    async def auth_middleware(self, request: Request, handler: Callable[[Request], Awaitable[Response]]) -> Response:
        # Skip auth for health checks and public routes
        if request.path in ["/health", "/api/auth/setup", "/api/auth/login", "/api/auth/refresh", "/api/auth/setup/status"]:
            return await handler(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await handler(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]

        # Check master key first
        master_check = await self.verify_master_key(token)
        if master_check:
            request["owner_id"] = "master"
            request["is_master_key"] = True
            return await handler(request)

        # Validate JWT token
        payload = await self.validate_token(token)
        if not payload:
            return json_response({"error": "unauthorized", "message": "Invalid or expired token"}, status=401)

        owner_id = payload.get("sub")
        if not owner_id:
            return json_response({"error": "unauthorized", "message": "Invalid token payload"}, status=401)

        request["owner_id"] = owner_id
        request["is_master_key"] = False
        request["session_id"] = payload.get("session_id")
        request["access_token"] = token

        return await handler(request)


# Global instance
auth_middleware_instance = AuthMiddleware()