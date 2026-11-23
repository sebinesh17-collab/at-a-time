"""
Master Orchestrator configuration with Cloudflare support
"""
from pydantic_settings import BaseSettings
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


class OrchestratorSettings(CloudflareAwareSettings if CLOUDFLARE_AVAILABLE else BaseSettings):
    # Database (auto-configured for Cloudflare)
    database_url: str = os.getenv("DATABASE_URL", "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge")

    # Redis (uses KV in Cloudflare)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change_this_in_production_min_32_chars")
    jwt_algorithm: str = "HS256"

    # Service URLs (auto-configured for Cloudflare)
    agent_registry_url: str = os.getenv("AGENT_REGISTRY_URL", "http://agent-registry:8003")
    task_scheduler_url: str = os.getenv("TASK_SCHEDULER_URL", "http://task-scheduler:8004")
    model_gateway_url: str = os.getenv("MODEL_GATEWAY_URL", "http://model-gateway:8005")
    file_service_url: str = os.getenv("FILE_SERVICE_URL", "http://file-service:8007")
    memory_service_url: str = os.getenv("MEMORY_SERVICE_URL", "http://memory-service:8008")
    knowledge_service_url: str = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8009")
    execution_service_url: str = os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8010")
    build_service_url: str = os.getenv("BUILD_SERVICE_URL", "http://build-service:8011")

    # Server
    host: str = "0.0.0.0"
    port: int = 8002

    # Orchestration
    max_concurrent_projects: int = 10
    task_decomposition_depth: int = 6
    default_task_timeout: int = 3600

    # Cloudflare-specific
    if CLOUDFLARE_AVAILABLE:
        cf_config: Optional[object] = None

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            if get_cloudflare_config:
                self.cf_config = get_cloudflare_config()
                # Override service URLs if in Cloudflare
                if self.cf_config.is_cloudflare:
                    service_urls = self.cf_config.service_urls
                    self.agent_registry_url = service_urls.get("AGENT_REGISTRY_URL", self.agent_registry_url)
                    self.task_scheduler_url = service_urls.get("TASK_SCHEDULER_URL", self.task_scheduler_url)
                    self.model_gateway_url = service_urls.get("MODEL_GATEWAY_URL", self.model_gateway_url)
                    self.file_service_url = service_urls.get("FILE_SERVICE_URL", self.file_service_url)
                    self.memory_service_url = service_urls.get("MEMORY_SERVICE_URL", self.memory_service_url)
                    self.knowledge_service_url = service_urls.get("KNOWLEDGE_SERVICE_URL", self.knowledge_service_url)
                    self.execution_service_url = service_urls.get("EXECUTION_SERVICE_URL", self.execution_service_url)
                    self.build_service_url = service_urls.get("BUILD_SERVICE_URL", self.build_service_url)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = OrchestratorSettings()