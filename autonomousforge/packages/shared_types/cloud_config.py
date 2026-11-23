"""
Cloud deployment configuration for AUTONOMOUSFORGE
Auto-detects deployment environment and configures database URLs, visual themes, and service endpoints
"""
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings


@dataclass
class CloudConfig:
    """Configuration for cloud deployment (Cloudflare Workers/Pages + D1/Hyperdrive)"""

    # Environment detection
    is_cloudflare: bool = field(default=False)
    is_cloudflare_pages: bool = field(default=False)
    is_cloudflare_worker: bool = field(default=False)
    is_local: bool = field(default=True)

    # Database configuration
    database_url: str = field(default="")
    database_type: str = field(default="postgresql")  # postgresql, d1, hyperdrive
    d1_database_id: Optional[str] = field(default=None)
    d1_database_name: str = field(default="autonomousforge")
    hyperdrive_connection_string: Optional[str] = field(default=None)

    # KV/R2 configuration
    kv_namespace_id: Optional[str] = field(default=None)
    kv_namespace_preview_id: Optional[str] = field(default=None)
    r2_bucket_name: str = field(default="autonomousforge-files")
    r2_bucket_preview_name: str = field(default="autonomousforge-files-preview")

    # Service bindings (for Workers)
    service_bindings: Dict[str, str] = field(default_factory=dict)

    # Visual theming
    theme_mode: str = field(default="auto")  # auto, dark, light, cloudflare
    primary_color: str = field(default="#7c3aed")  # Purple
    accent_color: str = field(default="#a855f7")
    background_color: str = field(default="#0f172a")
    surface_color: str = field(default="#1e293b")

    # API endpoints
    api_base_url: str = field(default="/api")
    ws_base_url: str = field(default="/ws")
    frontend_url: str = field(default="")
    api_domain: str = field(default="")

    # Feature flags
    enable_d1: bool = field(default=False)
    enable_r2: bool = field(default=False)
    enable_kv: bool = field(default=False)
    enable_hyperdrive: bool = field(default=False)
    enable_workers_ai: bool = field(default=False)
    enable_background_sync: bool = field(default=True)
    enable_push_notifications: bool = field(default=True)

    def __post_init__(self):
        self._detect_environment()
        self._configure_database()
        self._configure_visual_theme()
        self._configure_endpoints()

    def _detect_environment(self):
        """Auto-detect Cloudflare deployment environment"""
        # Cloudflare Workers environment variables
        cf_worker = os.getenv("CF_WORKER") == "true" or os.getenv("CF_PAGES") == "true"
        cf_pages = os.getenv("CF_PAGES") == "true"

        # Check for Cloudflare-specific env vars
        if cf_worker or os.getenv("CF_ACCOUNT_ID") or os.getenv("CF_PAGES_COMMIT_SHA"):
            self.is_cloudflare = True
            self.is_local = False

        if cf_pages:
            self.is_cloudflare_pages = True
            self.is_cloudflare_worker = False
        elif cf_worker:
            self.is_cloudflare_worker = True
            self.is_cloudflare_pages = False

        # Check for D1 binding
        if os.getenv("DB") or os.getenv("D1_DATABASE_ID"):
            self.enable_d1 = True
            self.d1_database_id = os.getenv("D1_DATABASE_ID") or os.getenv("DB")

        # Check for Hyperdrive
        if os.getenv("HYPERDRIVE_CONNECTION_STRING"):
            self.enable_hyperdrive = True
            self.hyperdrive_connection_string = os.getenv("HYPERDRIVE_CONNECTION_STRING")

        # Check for KV
        if os.getenv("SESSION_KV") or os.getenv("KV_NAMESPACE_ID"):
            self.enable_kv = True
            self.kv_namespace_id = os.getenv("KV_NAMESPACE_ID") or os.getenv("SESSION_KV")

        # Check for R2
        if os.getenv("FILE_STORAGE") or os.getenv("R2_BUCKET_NAME"):
            self.enable_r2 = True
            self.r2_bucket_name = os.getenv("R2_BUCKET_NAME") or "autonomousforge-files"

        # Check for Workers AI
        if os.getenv("AI") or os.getenv("WORKERS_AI"):
            self.enable_workers_ai = True

    def _configure_database(self):
        """Configure database URL based on environment"""
        if self.enable_hyperdrive and self.hyperdrive_connection_string:
            # Use Hyperdrive for PostgreSQL connection pooling
            self.database_url = self.hyperdrive_connection_string
            self.database_type = "hyperdrive"
        elif self.enable_d1 and self.d1_database_id:
            # Use Cloudflare D1 (SQLite-compatible)
            self.database_url = f"d1://{self.d1_database_id}"
            self.database_type = "d1"
        else:
            # Use standard PostgreSQL (local or via tunnel)
            self.database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge"
            )
            self.database_type = "postgresql"

    def _configure_visual_theme(self):
        """Configure visual theme based on deployment environment"""
        if self.is_cloudflare:
            # Cloudflare-themed colors
            self.theme_mode = "cloudflare"
            self.primary_color = "#f38020"  # Cloudflare orange
            self.accent_color = "#ff9500"
            self.background_color = "#0f172a"
            self.surface_color = "#1e293b"
        elif os.getenv("THEME_MODE"):
            self.theme_mode = os.getenv("THEME_MODE")
            self.primary_color = os.getenv("PRIMARY_COLOR", self.primary_color)
            self.accent_color = os.getenv("ACCENT_COLOR", self.accent_color)
            self.background_color = os.getenv("BACKGROUND_COLOR", self.background_color)
            self.surface_color = os.getenv("SURFACE_COLOR", self.surface_color)
        else:
            # Default purple theme (as requested)
            self.theme_mode = "purple"
            self.primary_color = "#7c3aed"
            self.accent_color = "#a855f7"
            self.background_color = "#0f172a"
            self.surface_color = "#1e293b"

    def _configure_endpoints(self):
        """Configure API and WebSocket endpoints"""
        if self.is_cloudflare_pages:
            # Frontend on Cloudflare Pages
            self.frontend_url = os.getenv("FRONTEND_URL", "https://autonomousforge.pages.dev")
            self.api_domain = os.getenv("API_DOMAIN", "api.yourdomain.com")
            self.api_base_url = f"https://{self.api_domain}/api"
            self.ws_base_url = f"wss://{self.api_domain}/ws"
        elif self.is_cloudflare_worker:
            # API on Cloudflare Workers
            self.api_domain = os.getenv("API_DOMAIN", "api.yourdomain.com")
            self.api_base_url = f"https://{self.api_domain}/api"
            self.ws_base_url = f"wss://{self.api_domain}/ws"
        else:
            # Local development
            self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            self.api_base_url = os.getenv("API_BASE_URL", "/api")
            self.ws_base_url = os.getenv("WS_BASE_URL", "/ws")

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for the current environment"""
        if self.database_type == "d1":
            return {
                "type": "d1",
                "database_id": self.d1_database_id,
                "database_name": self.d1_database_name,
                "binding": "DB",
            }
        elif self.database_type == "hyperdrive":
            return {
                "type": "hyperdrive",
                "connection_string": self.hyperdrive_connection_string,
            }
        else:
            return {
                "type": "postgresql",
                "url": self.database_url,
                "pool_size": 20,
                "max_overflow": 10,
            }

    def get_kv_config(self) -> Dict[str, Any]:
        """Get KV configuration"""
        return {
            "enabled": self.enable_kv,
            "namespace_id": self.kv_namespace_id,
            "preview_namespace_id": self.kv_namespace_preview_id,
            "binding": "SESSION_KV",
        }

    def get_r2_config(self) -> Dict[str, Any]:
        """Get R2 configuration"""
        return {
            "enabled": self.enable_r2,
            "bucket_name": self.r2_bucket_name,
            "preview_bucket_name": self.r2_bucket_preview_name,
            "binding": "FILE_STORAGE",
        }

    def get_visual_config(self) -> Dict[str, Any]:
        """Get visual theme configuration for frontend"""
        return {
            "theme_mode": self.theme_mode,
            "primary_color": self.primary_color,
            "accent_color": self.accent_color,
            "background_color": self.background_color,
            "surface_color": self.surface_color,
            "is_cloudflare": self.is_cloudflare,
        }

    def get_service_config(self) -> Dict[str, Any]:
        """Get service endpoint configuration"""
        if self.is_cloudflare:
            # In Cloudflare, use service bindings or HTTP to Workers
            return {
                "auth": os.getenv("AUTH_SERVICE_URL", f"https://{self.api_domain}/api/auth"),
                "orchestrator": os.getenv("ORCHESTRATOR_SERVICE_URL", f"https://{self.api_domain}/api/orchestrator"),
                "agents": os.getenv("AGENTS_SERVICE_URL", f"https://{self.api_domain}/api/agents"),
                "tasks": os.getenv("TASKS_SERVICE_URL", f"https://{self.api_domain}/api/tasks"),
                "models": os.getenv("MODELS_SERVICE_URL", f"https://{self.api_domain}/api/models"),
                "providers": os.getenv("PROVIDERS_SERVICE_URL", f"https://{self.api_domain}/api/providers"),
                "files": os.getenv("FILES_SERVICE_URL", f"https://{self.api_domain}/api/files"),
                "memory": os.getenv("MEMORY_SERVICE_URL", f"https://{self.api_domain}/api/memory"),
                "knowledge": os.getenv("KNOWLEDGE_SERVICE_URL", f"https://{self.api_domain}/api/knowledge"),
                "execution": os.getenv("EXECUTION_SERVICE_URL", f"https://{self.api_domain}/api/execution"),
                "build": os.getenv("BUILD_SERVICE_URL", f"https://{self.api_domain}/api/build"),
                "testing": os.getenv("TESTING_SERVICE_URL", f"https://{self.api_domain}/api/testing"),
                "monitoring": os.getenv("MONITORING_SERVICE_URL", f"https://{self.api_domain}/api/monitoring"),
            }
        else:
            # Local development - use Docker service names
            return {
                "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
                "orchestrator": os.getenv("MASTER_ORCHESTRATOR_URL", "http://master-orchestrator:8002"),
                "agents": os.getenv("AGENT_REGISTRY_URL", "http://agent-registry:8003"),
                "tasks": os.getenv("TASK_SCHEDULER_URL", "http://task-scheduler:8004"),
                "models": os.getenv("MODEL_GATEWAY_URL", "http://model-gateway:8005"),
                "providers": os.getenv("PROVIDER_SERVICE_URL", "http://provider-service:8006"),
                "files": os.getenv("FILE_SERVICE_URL", "http://file-service:8007"),
                "memory": os.getenv("MEMORY_SERVICE_URL", "http://memory-service:8008"),
                "knowledge": os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8009"),
                "execution": os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8010"),
                "build": os.getenv("BUILD_SERVICE_URL", "http://build-service:8011"),
                "testing": os.getenv("TESTING_SERVICE_URL", "http://testing-service:8012"),
                "monitoring": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8013"),
            }


# Global cloud config instance
cloud_config = CloudConfig()


def get_cloud_config() -> CloudConfig:
    """Get the global cloud configuration instance"""
    return cloud_config


def is_cloudflare_deployment() -> bool:
    """Check if running in Cloudflare environment"""
    return cloud_config.is_cloudflare


def get_database_url() -> str:
    """Get the configured database URL"""
    return cloud_config.database_url


def get_visual_theme() -> Dict[str, Any]:
    """Get visual theme configuration"""
    return cloud_config.get_visual_config()


def rewrite_database_url_for_cloud(url: str) -> str:
    """Rewrite database URL for cloud deployment"""
    if cloud_config.is_cloudflare:
        if cloud_config.enable_d1:
            return f"d1://{cloud_config.d1_database_id}"
        elif cloud_config.enable_hyperdrive:
            return cloud_config.hyperdrive_connection_string or url
    return url


def get_api_base_url() -> str:
    """Get the API base URL for the current environment"""
    return cloud_config.api_base_url


def get_ws_base_url() -> str:
    """Get the WebSocket base URL for the current environment"""
    return cloud_config.ws_base_url