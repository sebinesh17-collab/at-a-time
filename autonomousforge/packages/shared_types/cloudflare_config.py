"""
Cloudflare-specific configuration for Python backend services
Auto-detects Cloudflare deployment and configures database connections, bindings, and environment
"""
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings
from functools import lru_cache


@dataclass
class CloudflareBindings:
    """Cloudflare Workers bindings available in Python via workers-ai or FFI"""
    kv_namespaces: Dict[str, str] = field(default_factory=dict)  # name -> id
    r2_buckets: Dict[str, str] = field(default_factory=dict)  # name -> bucket_name
    d1_databases: Dict[str, str] = field(default_factory=dict)  # name -> database_id
    hyperdrive: Dict[str, str] = field(default_factory=dict)  # name -> id
    ai: Optional[str] = None  # Workers AI binding
    services: Dict[str, str] = field(default_factory=dict)  # service binding name -> service name
    durable_objects: Dict[str, str] = field(default_factory=dict)  # name -> class_name


class CloudflareConfig:
    """
    Configuration manager for Cloudflare deployment.
    Auto-detects environment and provides appropriate configuration.
    """

    def __init__(self):
        self._detected = False
        self._is_cloudflare = False
        self._is_pages = False
        self._is_worker = False
        self._bindings = CloudflareBindings()
        self._env_vars = {}
        self._database_config = {}
        self._visual_config = {}

    def detect(self) -> "CloudflareConfig":
        """Detect Cloudflare environment and configure accordingly"""
        if self._detected:
            return self

        # Check for Cloudflare environment indicators
        cf_env = os.getenv("CF_WORKER") == "true" or os.getenv("CF_PAGES") == "true"
        cf_account = bool(os.getenv("CF_ACCOUNT_ID"))
        cf_pages_commit = bool(os.getenv("CF_PAGES_COMMIT_SHA"))
        cf_worker_name = bool(os.getenv("CF_WORKER_NAME"))

        # Check for bindings (available in Workers runtime)
        has_kv = bool(os.getenv("SESSION_KV") or os.getenv("KV_NAMESPACE_ID"))
        has_r2 = bool(os.getenv("FILE_STORAGE") or os.getenv("R2_BUCKET_NAME"))
        has_d1 = bool(os.getenv("DB") or os.getenv("D1_DATABASE_ID"))
        has_hyperdrive = bool(os.getenv("HYPERDRIVE_CONNECTION_STRING") or os.getenv("HYPERDRIVE_ID"))
        has_ai = bool(os.getenv("AI") or os.getenv("WORKERS_AI"))

        self._is_cloudflare = cf_env or cf_account or cf_pages_commit or cf_worker_name or has_kv or has_r2 or has_d1 or has_hyperdrive or has_ai
        self._is_pages = cf_env and os.getenv("CF_PAGES") == "true"
        self._is_worker = cf_env and os.getenv("CF_WORKER") == "true"

        # Load bindings from environment
        self._load_bindings()

        # Configure database
        self._configure_database()

        # Configure visual theme
        self._configure_visual_theme()

        # Load service URLs
        self._load_service_urls()

        self._detected = True
        return self

    def _load_bindings(self):
        """Load Cloudflare bindings from environment"""
        # KV Namespaces
        if kv_id := os.getenv("SESSION_KV") or os.getenv("KV_NAMESPACE_ID"):
            self._bindings.kv_namespaces["SESSION_KV"] = kv_id
        if kv_id := os.getenv("CACHE_KV") or os.getenv("CACHE_KV_NAMESPACE_ID"):
            self._bindings.kv_namespaces["CACHE_KV"] = kv_id

        # R2 Buckets
        if bucket := os.getenv("FILE_STORAGE") or os.getenv("R2_BUCKET_NAME"):
            self._bindings.r2_buckets["FILE_STORAGE"] = bucket
        if bucket := os.getenv("BACKUP_BUCKET") or os.getenv("BACKUP_R2_BUCKET"):
            self._bindings.r2_buckets["BACKUP_BUCKET"] = bucket

        # D1 Databases
        if db_id := os.getenv("DB") or os.getenv("D1_DATABASE_ID"):
            self._bindings.d1_databases["DB"] = db_id
        if db_id := os.getenv("ANALYTICS_DB") or os.getenv("ANALYTICS_D1_ID"):
            self._bindings.d1_databases["ANALYTICS_DB"] = db_id

        # Hyperdrive
        if hd_id := os.getenv("HYPERDRIVE_ID"):
            self._bindings.hyperdrive["HYPERDRIVE"] = hd_id

        # Workers AI
        if ai := os.getenv("AI") or os.getenv("WORKERS_AI"):
            self._bindings.ai = ai

        # Service bindings
        for key, value in os.environ.items():
            if key.startswith("SERVICE_") and key.endswith("_NAME"):
                binding_name = key.replace("SERVICE_", "").replace("_NAME", "")
                self._bindings.services[binding_name] = value

        # Durable Objects
        for key, value in os.environ.items():
            if key.startswith("DO_") and key.endswith("_CLASS"):
                do_name = key.replace("DO_", "").replace("_CLASS", "")
                self._bindings.durable_objects[do_name] = value

    def _configure_database(self):
        """Configure database connection based on available bindings"""
        if self._bindings.d1_databases:
            # Use D1 (SQLite-compatible)
            db_id = list(self._bindings.d1_databases.values())[0]
            self._database_config = {
                "type": "d1",
                "database_id": db_id,
                "binding": list(self._bindings.d1_databases.keys())[0],
                "url": f"d1://{db_id}",
            }
        elif self._bindings.hyperdrive:
            # Use Hyperdrive for PostgreSQL
            hd_id = list(self._bindings.hyperdrive.values())[0]
            self._database_config = {
                "type": "hyperdrive",
                "hyperdrive_id": hd_id,
                "binding": list(self._bindings.hyperdrive.keys())[0],
                "url": os.getenv("HYPERDRIVE_CONNECTION_STRING", ""),
            }
        else:
            # Standard PostgreSQL (local or via tunnel)
            self._database_config = {
                "type": "postgresql",
                "url": os.getenv(
                    "DATABASE_URL",
                    "postgresql://forge:forge_secure_password@localhost:5432/autonomousforge"
                ),
                "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            }

    def _configure_visual_theme(self):
        """Configure visual theme for frontend"""
        theme_mode = os.getenv("THEME_MODE", "purple")
        primary_color = os.getenv("PRIMARY_COLOR", "#7c3aed")
        accent_color = os.getenv("ACCENT_COLOR", "#a855f7")

        if self._is_cloudflare and theme_mode == "cloudflare":
            primary_color = "#f38020"
            accent_color = "#ff9500"

        self._visual_config = {
            "theme_mode": theme_mode,
            "primary_color": primary_color,
            "accent_color": accent_color,
            "background_color": os.getenv("BACKGROUND_COLOR", "#0f172a"),
            "surface_color": os.getenv("SURFACE_COLOR", "#1e293b"),
            "is_cloudflare": self._is_cloudflare,
        }

    def _load_service_urls(self):
        """Load service URLs for inter-service communication"""
        self._env_vars = {
            "AUTH_SERVICE_URL": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
            "MASTER_ORCHESTRATOR_URL": os.getenv("MASTER_ORCHESTRATOR_URL", "http://master-orchestrator:8002"),
            "AGENT_REGISTRY_URL": os.getenv("AGENT_REGISTRY_URL", "http://agent-registry:8003"),
            "TASK_SCHEDULER_URL": os.getenv("TASK_SCHEDULER_URL", "http://task-scheduler:8004"),
            "MODEL_GATEWAY_URL": os.getenv("MODEL_GATEWAY_URL", "http://model-gateway:8005"),
            "PROVIDER_SERVICE_URL": os.getenv("PROVIDER_SERVICE_URL", "http://provider-service:8006"),
            "FILE_SERVICE_URL": os.getenv("FILE_SERVICE_URL", "http://file-service:8007"),
            "MEMORY_SERVICE_URL": os.getenv("MEMORY_SERVICE_URL", "http://memory-service:8008"),
            "KNOWLEDGE_SERVICE_URL": os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge-service:8009"),
            "EXECUTION_SERVICE_URL": os.getenv("EXECUTION_SERVICE_URL", "http://execution-service:8010"),
            "BUILD_SERVICE_URL": os.getenv("BUILD_SERVICE_URL", "http://build-service:8011"),
            "TESTING_SERVICE_URL": os.getenv("TESTING_SERVICE_URL", "http://testing-service:8012"),
            "MONITORING_SERVICE_URL": os.getenv("MONITORING_SERVICE_URL", "http://monitoring-service:8013"),
        }

        # Override for Cloudflare deployment
        if self._is_cloudflare:
            api_domain = os.getenv("API_DOMAIN", "api.yourdomain.com")
            for key in self._env_vars:
                service_name = key.replace("_SERVICE_URL", "").replace("_URL", "").lower()
                self._env_vars[key] = f"https://{api_domain}/api/{service_name}"

    @property
    def is_cloudflare(self) -> bool:
        return self._is_cloudflare

    @property
    def is_pages(self) -> bool:
        return self._is_pages

    @property
    def is_worker(self) -> bool:
        return self._is_worker

    @property
    def bindings(self) -> CloudflareBindings:
        return self._bindings

    @property
    def database_config(self) -> Dict[str, Any]:
        return self._database_config

    @property
    def visual_config(self) -> Dict[str, Any]:
        return self._visual_config

    @property
    def service_urls(self) -> Dict[str, str]:
        return self._env_vars

    def get_database_url(self) -> str:
        """Get the appropriate database URL for the current environment"""
        return self._database_config.get("url", "")

    def get_database_type(self) -> str:
        """Get the database type (postgresql, d1, hyperdrive)"""
        return self._database_config.get("type", "postgresql")

    def get_kv_namespace_id(self, name: str = "SESSION_KV") -> Optional[str]:
        """Get KV namespace ID by binding name"""
        return self._bindings.kv_namespaces.get(name)

    def get_r2_bucket_name(self, name: str = "FILE_STORAGE") -> Optional[str]:
        """Get R2 bucket name by binding name"""
        return self._bindings.r2_buckets.get(name)

    def get_d1_database_id(self, name: str = "DB") -> Optional[str]:
        """Get D1 database ID by binding name"""
        return self._bindings.d1_databases.get(name)

    def get_hyperdrive_id(self, name: str = "HYPERDRIVE") -> Optional[str]:
        """Get Hyperdrive ID by binding name"""
        return self._bindings.hyperdrive.get(name)

    def has_d1(self) -> bool:
        return bool(self._bindings.d1_databases)

    def has_hyperdrive(self) -> bool:
        return bool(self._bindings.hyperdrive)

    def has_kv(self) -> bool:
        return bool(self._bindings.kv_namespaces)

    def has_r2(self) -> bool:
        return bool(self._bindings.r2_buckets)

    def has_ai(self) -> bool:
        return self._bindings.ai is not None

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return {
            "is_cloudflare": self._is_cloudflare,
            "is_pages": self._is_pages,
            "is_worker": self._is_worker,
            "database": self._database_config,
            "visual": self._visual_config,
            "bindings": {
                "kv": self._bindings.kv_namespaces,
                "r2": self._bindings.r2_buckets,
                "d1": self._bindings.d1_databases,
                "hyperdrive": self._bindings.hyperdrive,
                "ai": self._bindings.ai is not None,
                "services": self._bindings.services,
                "durable_objects": self._bindings.durable_objects,
            },
            "services": self._env_vars,
        }


# Global instance
_cf_config: Optional[CloudflareConfig] = None


def get_cloudflare_config() -> CloudflareConfig:
    """Get the global Cloudflare configuration instance"""
    global _cf_config
    if _cf_config is None:
        _cf_config = CloudflareConfig().detect()
    return _cf_config


def is_cloudflare_deployment() -> bool:
    """Check if running in Cloudflare environment"""
    return get_cloudflare_config().is_cloudflare


def get_database_url() -> str:
    """Get the configured database URL"""
    return get_cloudflare_config().get_database_url()


def get_database_type() -> str:
    """Get the database type"""
    return get_cloudflare_config().get_database_type()


def get_visual_theme() -> Dict[str, Any]:
    """Get visual theme configuration"""
    return get_cloudflare_config().visual_config


def get_service_url(service: str) -> str:
    """Get service URL by name"""
    key = f"{service.upper()}_SERVICE_URL"
    return get_cloudflare_config().service_urls.get(key, "")


def rewrite_database_url(url: str) -> str:
    """Rewrite database URL for Cloudflare deployment"""
    config = get_cloudflare_config()
    if config.is_cloudflare:
        if config.has_d1():
            return f"d1://{config.get_d1_database_id()}"
        elif config.has_hyperdrive():
            return config.database_config.get("url", url)
    return url


# Integration with service config classes
class CloudflareAwareSettings(BaseSettings):
    """Base settings class that auto-configures for Cloudflare"""

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        # Get Cloudflare config
        cf = get_cloudflare_config()

        # Override database URL if in Cloudflare
        if cf.is_cloudflare:
            if "database_url" not in kwargs:
                kwargs["database_url"] = cf.get_database_url()

            # Override Redis URL if KV available
            if cf.has_kv() and "redis_url" not in kwargs:
                kwargs["redis_url"] = "kv://session"  # Special marker for KV

        super().__init__(**kwargs)

    @property
    def cloudflare(self) -> CloudflareConfig:
        return get_cloudflare_config()

    def get_database_config(self) -> Dict[str, Any]:
        return self.cloudflare.database_config

    def get_service_urls(self) -> Dict[str, str]:
        return self.cloudflare.service_urls