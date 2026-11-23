"""
Model Gateway configuration with Cloudflare support
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


class ModelGatewaySettings(CloudflareAwareSettings if CLOUDFLARE_AVAILABLE else BaseSettings):
    # Database (auto-configured for Cloudflare)
    database_url: str = os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")

    # Redis (uses KV in Cloudflare)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Server
    host: str = "0.0.0.0"
    port: int = 8005

    # NVIDIA NIM
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    # Default models
    default_model: str = "nemotron-3-ultra"
    default_provider: str = "nvidia"

    # Rate limiting
    max_concurrent_requests: int = 50
    request_timeout_seconds: int = 120

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


settings = ModelGatewaySettings()