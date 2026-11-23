"""
Rate limiting middleware for API Gateway
"""
import time
from typing import Optional, Dict, Tuple
import redis.asyncio as redis

from ..config import settings


class RateLimiter:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Tuple[int, float]] = {}  # key -> (count, window_start)
        self.cache_ttl = 1  # seconds

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

    def _get_client_key(self, request) -> str:
        """Get unique key for client"""
        # Use owner_id if available (from auth middleware)
        owner_id = request.get("owner_id", "anonymous")
        # Include path for path-based limiting
        path = request.path
        return f"ratelimit:{owner_id}:{path}"

    async def check_rate_limit(self, request) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limit.
        Returns (allowed, headers_dict)
        """
        key = self._get_client_key(request)
        now = time.time()
        window = settings.default_rate_window
        limit = settings.default_rate_limit

        # Try Redis first
        if self.redis_client:
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                results = await pipe.execute()
                current_count = results[0]

                remaining = max(0, limit - current_count)
                reset_time = int(now) + window

                headers = {
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_time),
                }

                return current_count <= limit, headers
            except Exception:
                # Fall back to local cache on Redis error
                pass

        # Local in-memory fallback (per process)
        if key in self.local_cache:
            count, window_start = self.local_cache[key]
            if now - window_start < window:
                current_count = count + 1
                self.local_cache[key] = (current_count, window_start)
            else:
                current_count = 1
                self.local_cache[key] = (current_count, now)
        else:
            current_count = 1
            self.local_cache[key] = (current_count, now)

        # Clean old entries periodically
        if len(self.local_cache) > 10000:
            cutoff = now - window
            self.local_cache = {k: v for k, v in self.local_cache.items() if v[1] > cutoff}

        remaining = max(0, limit - current_count)
        reset_time = int(now) + window

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        return current_count <= limit, headers


rate_limiter = RateLimiter()