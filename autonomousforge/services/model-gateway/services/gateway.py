"""
Model Gateway Service - NVIDIA NIM API integration and model management
"""
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator
from uuid import uuid4

import aiohttp

from ..database import db
from ..config import settings

logger = logging.getLogger(__name__)


class ModelGateway:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.providers: Dict[str, Dict] = {}
        self.models: Dict[str, Dict] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def initialize(self):
        """Initialize gateway"""
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
        )
        await self._load_providers()
        await self._load_models()
        logger.info("Model gateway initialized")

    async def shutdown(self):
        """Shutdown gateway"""
        if self.session:
            await self.session.close()
        logger.info("Model gateway shut down")

    async def _load_providers(self):
        """Load providers from database"""
        rows = await db.fetch("SELECT * FROM model_providers WHERE is_active = true")
        for row in rows:
            provider = dict(row)
            self.providers[provider["id"]] = provider
            # Decrypt API key
            provider["api_key"] = await self._decrypt_api_key(provider["api_key_encrypted"])
        logger.info(f"Loaded {len(self.providers)} providers")

    async def _load_models(self):
        """Load models from database"""
        rows = await db.fetch("SELECT * FROM models WHERE is_active = true")
        for row in rows:
            model = dict(row)
            self.models[model["id"]] = model
        logger.info(f"Loaded {len(self.models)} models")

    async def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key (placeholder - implement proper encryption)"""
        # In production, use proper encryption like Fernet
        return encrypted_key

    async def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key (placeholder - implement proper encryption)"""
        return api_key

    # ==================== Provider Management ====================

    async def register_provider(self, provider_data: Dict) -> Dict:
        """Register a new model provider"""
        provider_id = str(uuid4())
        now = datetime.utcnow()

        encrypted_key = await self._encrypt_api_key(provider_data["api_key"])

        await db.execute("""
            INSERT INTO model_providers (id, name, provider_type, base_url, api_key_encrypted,
                                        is_active, priority, config, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, provider_id, provider_data["name"], provider_data["provider_type"],
            provider_data.get("base_url"), encrypted_key,
            provider_data.get("is_active", True),
            provider_data.get("priority", 10),
            json.dumps(provider_data.get("config", {})),
            now, now)

        provider = await self.get_provider(provider_id)
        self.providers[provider_id] = provider
        return provider

    async def get_provider(self, provider_id: str) -> Optional[Dict]:
        """Get provider by ID"""
        row = await db.fetchrow("SELECT * FROM model_providers WHERE id = $1", provider_id)
        return dict(row) if row else None

    async def list_providers(self) -> List[Dict]:
        """List all providers"""
        rows = await db.fetch("SELECT * FROM model_providers ORDER BY priority, created_at")
        return [dict(row) for row in rows]

    async def update_provider(self, provider_id: str, updates: Dict) -> Optional[Dict]:
        """Update provider"""
        allowed = ["name", "base_url", "is_active", "priority", "config"]
        set_clauses = []
        params = [provider_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(json.dumps(updates[field]) if isinstance(updates[field], dict) else updates[field])
                param_idx += 1

        if "api_key" in updates:
            set_clauses.append("api_key_encrypted = $2")
            params[1] = await self._encrypt_api_key(updates["api_key"])
            param_idx = 3

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE model_providers SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)

        provider = await self.get_provider(provider_id)
        if provider:
            self.providers[provider_id] = provider
        return provider

    async def delete_provider(self, provider_id: str) -> bool:
        """Delete provider"""
        result = await db.execute("DELETE FROM model_providers WHERE id = $1", provider_id)
        if result != "DELETE 0":
            self.providers.pop(provider_id, None)
            return True
        return False

    # ==================== Model Management ====================

    async def register_model(self, model_data: Dict) -> Dict:
        """Register a new model"""
        model_id = str(uuid4())
        now = datetime.utcnow()

        await db.execute("""
            INSERT INTO models (id, provider_id, model_id, display_name, model_type,
                               context_window, max_output_tokens, capabilities, pricing,
                               is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, model_id, model_data["provider_id"], model_data["model_id"],
            model_data.get("display_name"), model_data.get("model_type", "chat"),
            model_data.get("context_window", 8192),
            model_data.get("max_output_tokens", 4096),
            json.dumps(model_data.get("capabilities", [])),
            json.dumps(model_data.get("pricing", {})),
            model_data.get("is_active", True),
            now, now)

        model = await self.get_model(model_id)
        self.models[model_id] = model
        return model

    async def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model by ID"""
        row = await db.fetchrow("SELECT * FROM models WHERE id = $1", model_id)
        return dict(row) if row else None

    async def list_models(self, provider_id: str = None, model_type: str = None) -> List[Dict]:
        """List models with filters"""
        query = "SELECT * FROM models WHERE is_active = true"
        params = []
        param_idx = 1

        if provider_id:
            query += f" AND provider_id = ${param_idx}"
            params.append(provider_id)
            param_idx += 1

        if model_type:
            query += f" AND model_type = ${param_idx}"
            params.append(model_type)
            param_idx += 1

        query += " ORDER BY created_at"
        rows = await db.fetch(query, *params)
        return [dict(row) for row in rows]

    async def update_model(self, model_id: str, updates: Dict) -> Optional[Dict]:
        """Update model"""
        allowed = ["display_name", "context_window", "max_output_tokens", "capabilities", "pricing", "is_active"]
        set_clauses = []
        params = [model_id]
        param_idx = 2

        for field in allowed:
            if field in updates:
                set_clauses.append(f"{field} = ${param_idx}")
                params.append(json.dumps(updates[field]) if isinstance(updates[field], (dict, list)) else updates[field])
                param_idx += 1

        if not set_clauses:
            return None

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE models SET {', '.join(set_clauses)} WHERE id = $1"
        await db.execute(query, *params)

        model = await self.get_model(model_id)
        if model:
            self.models[model_id] = model
        return model

    async def delete_model(self, model_id: str) -> bool:
        """Delete model"""
        result = await db.execute("DELETE FROM models WHERE id = $1", model_id)
        if result != "DELETE 0":
            self.models.pop(model_id, None)
            return True
        return False

    # ==================== Completion API ====================

    async def complete(self, request_data: Dict) -> Dict:
        """Generate completion"""
        async with self._semaphore:
            model_id = request_data.get("model", settings.default_model)
            model = self.models.get(model_id)

            if not model:
                # Try to find by model_id field
                for m in self.models.values():
                    if m["model_id"] == model_id:
                        model = m
                        break

            if not model:
                raise ValueError(f"Model not found: {model_id}")

            provider = self.providers.get(model["provider_id"])
            if not provider:
                raise ValueError(f"Provider not found for model: {model_id}")

            # Prepare request
            messages = request_data.get("messages", [])
            temperature = request_data.get("temperature", 0.7)
            max_tokens = request_data.get("max_tokens", model.get("max_output_tokens", 4096))
            stream = request_data.get("stream", False)

            start_time = time.time()

            if provider["provider_type"] == "nvidia":
                return await self._complete_nvidia(provider, model, messages, temperature, max_tokens, stream)
            elif provider["provider_type"] == "openai":
                return await self._complete_openai(provider, model, messages, temperature, max_tokens, stream)
            elif provider["provider_type"] == "anthropic":
                return await self._complete_anthropic(provider, model, messages, temperature, max_tokens, stream)
            else:
                raise ValueError(f"Unsupported provider type: {provider['provider_type']}")

    async def _complete_nvidia(self, provider: Dict, model: Dict, messages: List[Dict],
                               temperature: float, max_tokens: int, stream: bool) -> Dict:
        """Complete using NVIDIA NIM API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model["model_id"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        url = f"{provider['base_url'] or settings.nvidia_base_url}/chat/completions"

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"NVIDIA API error: {response.status} - {error_text}")

            if stream:
                # Return async generator for streaming
                return {"stream": self._stream_nvidia_response(response)}

            data = await response.json()
            return self._format_completion_response(data, model)

    async def _stream_nvidia_response(self, response: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        """Stream NVIDIA response"""
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                yield data

    async def _complete_openai(self, provider: Dict, model: Dict, messages: List[Dict],
                               temperature: float, max_tokens: int, stream: bool) -> Dict:
        """Complete using OpenAI-compatible API"""
        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model["model_id"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        url = f"{provider['base_url'] or 'https://api.openai.com/v1'}/chat/completions"

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenAI API error: {response.status} - {error_text}")

            if stream:
                return {"stream": self._stream_openai_response(response)}

            data = await response.json()
            return self._format_completion_response(data, model)

    async def _stream_openai_response(self, response: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        """Stream OpenAI response"""
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                yield data

    async def _complete_anthropic(self, provider: Dict, model: Dict, messages: List[Dict],
                                  temperature: float, max_tokens: int, stream: bool) -> Dict:
        """Complete using Anthropic API"""
        # Convert messages to Anthropic format
        system_message = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        headers = {
            "x-api-key": provider["api_key"],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model["model_id"],
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }

        if system_message:
            payload["system"] = system_message

        url = f"{provider['base_url'] or 'https://api.anthropic.com/v1'}/messages"

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic API error: {response.status} - {error_text}")

            if stream:
                return {"stream": self._stream_anthropic_response(response)}

            data = await response.json()
            return self._format_anthropic_response(data, model)

    async def _stream_anthropic_response(self, response: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        """Stream Anthropic response"""
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                yield data

    def _format_completion_response(self, data: Dict, model: Dict) -> Dict:
        """Format completion response to standard format"""
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})

        return {
            "id": data.get("id", str(uuid4())),
            "model": model["id"],
            "content": choice.get("message", {}).get("content", ""),
            "role": "assistant",
            "finish_reason": choice.get("finish_reason", "stop"),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        }

    def _format_anthropic_response(self, data: Dict, model: Dict) -> Dict:
        """Format Anthropic response to standard format"""
        usage = data.get("usage", {})

        return {
            "id": data.get("id", str(uuid4())),
            "model": model["id"],
            "content": data.get("content", [{}])[0].get("text", ""),
            "role": "assistant",
            "finish_reason": data.get("stop_reason", "end_turn"),
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            }
        }

    # ==================== Embeddings ====================

    async def embed(self, request_data: Dict) -> Dict:
        """Generate embeddings"""
        model_id = request_data.get("model")
        input_text = request_data.get("input")

        if not model_id or not input_text:
            raise ValueError("model and input required")

        model = self.models.get(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")

        provider = self.providers.get(model["provider_id"])
        if not provider:
            raise ValueError(f"Provider not found for model: {model_id}")

        # For now, use a simple embedding approach
        # In production, call appropriate embedding API
        return {
            "model": model["id"],
            "embeddings": [[0.0] * 1536],  # Placeholder
            "usage": {"prompt_tokens": len(str(input_text)), "total_tokens": len(str(input_text))}
        }

    # ==================== Usage Tracking ====================

    async def log_usage(self, usage_data: Dict):
        """Log API usage"""
        await db.execute("""
            INSERT INTO api_usage_logs (id, model_id, provider_id, request_tokens,
                                       response_tokens, total_tokens, latency_ms,
                                       status, error, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, str(uuid4()), usage_data.get("model_id"), usage_data.get("provider_id"),
            usage_data.get("prompt_tokens", 0), usage_data.get("completion_tokens", 0),
            usage_data.get("total_tokens", 0), usage_data.get("latency_ms", 0),
            usage_data.get("status", "success"), usage_data.get("error"),
            datetime.utcnow())


gateway = ModelGateway()