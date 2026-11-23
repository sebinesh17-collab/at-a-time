"""
Auth service configuration with Cloudflare support
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
import sys

# Add shared-types to path for cloudflare config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared-types"))

try:
    from cloudflare_config import CloudflareAwareSettings, get_cloudflare_config
    CLOUDFLARE_AVAILABLE = True
except ImportError:
    CLOUDFLARE_AVAILABLE = False
    CloudflareAwareSettings = BaseSettings
    get_cloudflare_config = None


class AuthSettings(CloudflareAwareSettings if CLOUDFLARE_AVAILABLE else BaseSettings):
    # Database (auto-configured for Cloudflare)
    database_url: str = os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")

    # Redis (uses KV in Cloudflare)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change_this_in_production_min_32_chars")
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    refresh_token_expiry_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "7"))

    # Security
    argon2_time_cost: int = int(os.getenv("ARGON2_TIME_COST", "3"))
    argon2_memory_cost: int = int(os.getenv("ARGON2_MEMORY_COST", "65536"))
    argon2_parallelism: int = int(os.getenv("ARGON2_PARALLELISM", "4"))

    # Rate limiting
    login_rate_limit: int = int(os.getenv("LOGIN_RATE_LIMIT", "5"))
    login_rate_window_minutes: int = int(os.getenv("LOGIN_RATE_WINDOW_MINUTES", "15"))
    api_rate_limit: int = int(os.getenv("API_RATE_LIMIT", "100"))
    api_rate_window_minutes: int = int(os.getenv("API_RATE_WINDOW_MINUTES", "1"))

    # Master API Key
    master_api_key: Optional[str] = os.getenv("MASTER_API_KEY")

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # Cloudflare-specific
    if CLOUDFLARE_AVAILABLE:
        cf_config: Optional[object] = None

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if get_cloudflare_config:
                self.cf_config = get_cloudflare_config()

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = AuthSettings()