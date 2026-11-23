"""
Provider Service - API key vault and provider management
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from cryptography.fernet import Fernet

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self):
        self._fernet: Optional[Fernet] = None

    async def initialize(self):
        """Initialize encryption"""
        key = settings.encryption_key.encode()
        # Ensure key is 32 bytes
        if len(key) < 32:
            key = key.ljust(32, b'0')
        elif len(key) > 32:
            key = key[:32]
        self._fernet = Fernet(key[:32].ljust(44, b'='))  # Fernet needs 32 bytes base64 encoded
        logger.info("Provider service initialized")

    def _encrypt(self, value: str) -> str:
        """Encrypt a value"""
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        return self._fernet.encrypt(value.encode()).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not self._fernet:
            raise RuntimeError("Encryption not initialized")
        return self._fernet.decrypt(encrypted_value.encode()).decode()

    # ==================== API Key Vault ====================

    async def store_api_key(self, key_data: Dict) -> Dict:
        """Store an encrypted API key"""
        key_id = str(uuid4())
        now = datetime.utcnow()

        encrypted_key = self._encrypt(key_data["api_key"])

        await db.execute("""
            INSERT INTO api_keys (id, name, provider, key_type, api_key_encrypted,
                                 metadata, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, key_id, key_data["name"], key_data.get("provider"),
            key_data.get("key_type", "api_key"), encrypted_key,
            key_data.get("metadata", {}), key_data.get("is_active", True),
            now, now)

        return await self.get_api_key(key_id)

    async def get_api_key(self, key_id: str) -> Optional[Dict]:
        """Get API key by ID (decrypted)"""
        row = await db.fetchrow("SELECT * FROM api_keys WHERE id = $1", key_id)
        if not row:
            return None

        key = dict(row)
        key["api_key"] = self._decrypt(key["api_key_encrypted"])
        key.pop("api_key_encrypted", None)
        return key

    async def get_api_key_for_provider(self, provider: str, key_type: str = "api_key") -> Optional[str]:
        """Get decrypted API key for a provider"""
        row = await db.fetchrow("""
            SELECT api_key_encrypted FROM api_keys
            WHERE provider = $1 AND key_type = $2 AND is_active = true
            ORDER BY created_at DESC LIMIT 1
        """, provider, key_type)

        if row:
            return self._decrypt(row["api_key_encrypted"])
        return None

    async def list_api_keys(self, provider: str = None, include_keys: bool = False) -> List[Dict]:
        """List API keys"""
        query = "SELECT * FROM api_keys WHERE 1=1"
        params = []
        param_idx = 1

        if provider:
            query += f" AND provider = ${param_idx}"
            params.append(provider)
            param_idx += 1

        query += " ORDER BY created_at DESC"
        rows = await db.fetch(query, *params)

        keys = []
        for row in rows:
            key = dict(row)
            if include_keys:
                key["api_key"] = self._decrypt(key["api_key_encrypted"])
            key.pop("api_key_encrypted", None)
            keys.append(key)
        return keys

    async def update_api_key(self, key_id: str, updates: Dict) -> Optional[Dict]:
        """Update API key"""
        allowed = ["name", "provider", "key_type", "metadata", "is_active"]
        set_clauses = []
        params = [key_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(updates[field])
                param_idx += 1

        if "api_key" in updates:
            set_clauses.append("api_key_encrypted = $2")
            params[1] = self._encrypt(updates["api_key"])
            param_idx = 3

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE api_keys SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_api_key(key_id)

    async def delete_api_key(self, key_id: str) -> bool:
        """Delete API key"""
        result = await db.execute("DELETE FROM api_keys WHERE id = $1", key_id)
        return result != "DELETE 0"

    # ==================== Provider Configuration ====================

    async def save_provider_config(self, config_data: Dict) -> Dict:
        """Save provider configuration"""
        config_id = str(uuid4())
        now = datetime.utcnow()

        # Encrypt sensitive fields
        config = config_data.copy()
        encrypted_fields = {}
        for field in ["api_key", "secret_key", "access_token", "refresh_token"]:
            if field in config and config[field]:
                encrypted_fields[field] = self._encrypt(config[field])
                config.pop(field)

        await db.execute("""
            INSERT INTO provider_configs (id, provider, config_name, config_data,
                                         encrypted_fields, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, config_id, config_data["provider"], config_data.get("config_name", "default"),
            config, encrypted_fields, config_data.get("is_active", True), now, now)

        return await self.get_provider_config(config_id)

    async def get_provider_config(self, config_id: str) -> Optional[Dict]:
        """Get provider configuration"""
        row = await db.fetchrow("SELECT * FROM provider_configs WHERE id = $1", config_id)
        if not row:
            return None

        config = dict(row)
        # Decrypt sensitive fields
        for field, encrypted_value in config.get("encrypted_fields", {}).items():
            config[field] = self._decrypt(encrypted_value)
        config.pop("encrypted_fields", None)
        return config

    async def get_provider_config_by_name(self, provider: str, config_name: str = "default") -> Optional[Dict]:
        """Get provider configuration by name"""
        row = await db.fetchrow("""
            SELECT * FROM provider_configs
            WHERE provider = $1 AND config_name = $2 AND is_active = true
            ORDER BY updated_at DESC LIMIT 1
        """, provider, config_name)

        if not row:
            return None

        config = dict(row)
        for field, encrypted_value in config.get("encrypted_fields", {}).items():
            config[field] = self._decrypt(encrypted_value)
        config.pop("encrypted_fields", None)
        return config

    async def list_provider_configs(self, provider: str = None) -> List[Dict]:
        """List provider configurations"""
        query = "SELECT * FROM provider_configs WHERE 1=1"
        params = []
        param_idx = 1

        if provider:
            query += f" AND provider = ${param_idx}"
            params.append(provider)
            param_idx += 1

        query += " ORDER BY provider, config_name"
        rows = await db.fetch(query, *params)

        configs = []
        for row in rows:
            config = dict(row)
            config.pop("encrypted_fields", None)
            configs.append(config)
        return configs

    async def update_provider_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        """Update provider configuration"""
        allowed = ["config_name", "config_data", "is_active"]
        set_clauses = []
        params = [config_id]
        param_idx = 2

        encrypted_fields = {}
        for field in allowed:
            if field in updates:
                if field == "config_data":
                    # Encrypt sensitive fields in config_data
                    config = updates[field].copy()
                    for enc_field in ["api_key", "secret_key", "access_token", "refresh_token"]:
                        if enc_field in config and config[enc_field]:
                            encrypted_fields[enc_field] = self._encrypt(config[enc_field])
                            config.pop(enc_field)
                    set_clauses.append(f"config_data = ${param_idx}")
                    params.append(config)
                    if encrypted_fields:
                        set_clauses.append(f"encrypted_fields = ${param_idx + 1}")
                        params.append(encrypted_fields)
                    param_idx += 2
                else:
                    set_clauses.append(f"{field} = ${param_idx}")
                    params.append(updates[field])
                    param_idx += 1

        # Handle direct encrypted field updates
        for field in ["api_key", "secret_key", "access_token", "refresh_token"]:
            if field in updates and updates[field]:
                encrypted_fields[field] = self._encrypt(updates[field])

        if encrypted_fields and "encrypted_fields" not in [c.split("=")[0].strip() for c in set_clauses]:
            set_clauses.append(f"encrypted_fields = ${param_idx}")
            params.append(encrypted_fields)
            param_idx += 1

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE provider_configs SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)
        return await self.get_provider_config(config_id)

    async def delete_provider_config(self, config_id: str) -> bool:
        """Delete provider configuration"""
        result = await db.execute("DELETE FROM provider_configs WHERE id = $1", config_id)
        return result != "DELETE 0"

    # ==================== Model Registry (for model gateway) ====================

    async def register_model_provider(self, provider_data: Dict) -> Dict:
        """Register a model provider (for model gateway)"""
        provider_id = str(uuid4())
        now = datetime.utcnow()

        encrypted_key = self._encrypt(provider_data["api_key"])

        await db.execute("""
            INSERT INTO model_providers (id, name, provider_type, base_url, api_key_encrypted,
                                        is_active, priority, config, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, provider_id, provider_data["name"], provider_data["provider_type"],
            provider_data.get("base_url"), encrypted_key,
            provider_data.get("is_active", True),
            provider_data.get("priority", 10),
            provider_data.get("config", {}),
            now, now)

        row = await db.fetchrow("SELECT * FROM model_providers WHERE id = $1", provider_id)
        provider = dict(row)
        provider["api_key"] = provider_data["api_key"]  # Return decrypted for immediate use
        provider.pop("api_key_encrypted", None)
        return provider

    async def get_model_provider(self, provider_id: str) -> Optional[Dict]:
        """Get model provider by ID"""
        row = await db.fetchrow("SELECT * FROM model_providers WHERE id = $1", provider_id)
        if not row:
            return None
        provider = dict(row)
        provider["api_key"] = self._decrypt(provider["api_key_encrypted"])
        provider.pop("api_key_encrypted", None)
        return provider

    async def list_model_providers(self) -> List[Dict]:
        """List model providers"""
        rows = await db.fetch("SELECT * FROM model_providers ORDER BY priority, created_at")
        providers = []
        for row in rows:
            provider = dict(row)
            provider.pop("api_key_encrypted", None)
            providers.append(provider)
        return providers


provider_service = ProviderService()