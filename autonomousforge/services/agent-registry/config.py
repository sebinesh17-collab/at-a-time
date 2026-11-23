"""
Agent Registry configuration with Cloudflare support
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


class AgentRegistrySettings(CloudflareAwareSettings if CLOUDFLARE_AVAILABLE else BaseSettings):
    # Database (auto-configured for Cloudflare)
    database_url: str = os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")

    # Redis (uses KV in Cloudflare)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change_this_in_production_min_32_chars")
    jwt_algorithm: str = "HS256"

    # Server
    host: str = "0.0.0.0"
    port: int = 8003

    # Agent Hierarchy
    total_agents: int = 16111
    master_count: int = 1
    principal_count: int = 10
    head_count: int = 100
    team_leader_count: int = 1000
    worker_count: int = 15000

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


settings = AgentRegistrySettings()