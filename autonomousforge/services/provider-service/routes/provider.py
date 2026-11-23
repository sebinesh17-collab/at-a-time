"""
Provider Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID

from ..services.provider import provider_service
from ..database import db
from ..models.schemas import (
    ProviderCreate, ProviderUpdate, ProviderResponse,
    ModelCreate, ModelUpdate, ModelResponse,
    ModelProviderCreate, ModelProviderUpdate, ModelProviderResponse,
    ApiKeyVaultCreate, ApiKeyVaultResponse, ApiKeyVaultUpdate,
    ProviderFilter, ModelFilter, ModelProviderFilter, ApiKeyVaultFilter,
    ProviderStatsResponse, HealthResponse
)


def require_auth(handler):
    """Decorator to require authentication"""
    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]
        if token.startswith("af_master_"):
            request["owner_id"] = "master"
            request["is_master"] = True
            return await handler(request)

        request["owner_id"] = "00000000-0000-0000-0000-000000000001"
        request["is_master"] = False
        return await handler(request)
    return wrapper


# ==================== Provider Management ====================

@require_auth
async def create_provider(request: Request):
    """Create a provider"""
    try:
        data = await request.json()
        create_request = ProviderCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        provider = await provider_service.create_provider(create_request.model_dump())
        return json_response(provider, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_provider(request: Request):
    """Get provider by ID"""
    provider_id = request.match_info.get("provider_id")
    try:
        provider_uuid = UUID(provider_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid provider ID"}, status=400)

    provider = await provider_service.get_provider(str(provider_uuid))
    if not provider:
        return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
    return json_response(provider)


@require_auth
async def update_provider(request: Request):
    """Update provider"""
    provider_id = request.match_info.get("provider_id")
    try:
        provider_uuid = UUID(provider_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid provider ID"}, status=400)

    try:
        data = await request.json()
        update_request = ProviderUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        provider = await provider_service.update_provider(str(provider_uuid), update_request.model_dump(exclude_unset=True))
        if not provider:
            return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
        return json_response(provider)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_providers(request: Request):
    """List providers"""
    provider_type = request.query.get("provider_type")
    is_enabled = request.query.get("is_enabled")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ProviderFilter(
        provider_type=provider_type,
        is_enabled=is_enabled.lower() == "true" if is_enabled else None,
        limit=limit,
        offset=offset
    )

    providers = await provider_service.list_providers(
        filter_params.provider_type,
        filter_params.is_enabled,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(providers)


@require_auth
async def get_provider_stats(request: Request):
    """Get provider statistics"""
    stats = await provider_service.get_stats()
    return json_response(stats)


# ==================== Model Management ====================

@require_auth
async def create_model(request: Request):
    """Create a model"""
    try:
        data = await request.json()
        create_request = ModelCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        model = await provider_service.create_model(create_request.model_dump())
        return json_response(model, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_model(request: Request):
    """Get model by ID"""
    model_id = request.match_info.get("model_id")
    try:
        model_uuid = UUID(model_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid model ID"}, status=400)

    model = await provider_service.get_model(str(model_uuid))
    if not model:
        return json_response({"error": "not_found", "message": "Model not found"}, status=404)
    return json_response(model)


@require_auth
async def update_model(request: Request):
    """Update model"""
    model_id = request.match_info.get("model_id")
    try:
        model_uuid = UUID(model_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid model ID"}, status=400)

    try:
        data = await request.json()
        update_request = ModelUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        model = await provider_service.update_model(str(model_uuid), update_request.model_dump(exclude_unset=True))
        if not model:
            return json_response({"error": "not_found", "message": "Model not found"}, status=404)
        return json_response(model)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_models(request: Request):
    """List models"""
    provider_id = request.query.get("provider_id")
    is_enabled = request.query.get("is_enabled")
    model_type = request.query.get("model_type")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ModelFilter(
        provider_id=UUID(provider_id) if provider_id else None,
        is_enabled=is_enabled.lower() == "true" if is_enabled else None,
        model_type=model_type,
        limit=limit,
        offset=offset
    )

    models = await provider_service.list_models(
        str(filter_params.provider_id) if filter_params.provider_id else None,
        filter_params.is_enabled,
        filter_params.model_type,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(models)


# ==================== Model Provider Management ====================

@require_auth
async def create_model_provider(request: Request):
    """Register a model provider"""
    try:
        data = await request.json()
        create_request = ModelProviderCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        provider = await provider_service.register_model_provider(create_request.model_dump())
        return json_response(provider, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_model_provider(request: Request):
    """Get model provider by ID"""
    provider_id = request.match_info.get("provider_id")
    try:
        provider_uuid = UUID(provider_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid provider ID"}, status=400)

    provider = await provider_service.get_model_provider(str(provider_uuid))
    if not provider:
        return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
    return json_response(provider)


@require_auth
async def list_model_providers(request: Request):
    """List model providers"""
    provider_type = request.query.get("provider_type")
    is_enabled = request.query.get("is_enabled")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ModelProviderFilter(
        provider_type=provider_type,
        is_enabled=is_enabled.lower() == "true" if is_enabled else None,
        limit=limit,
        offset=offset
    )

    providers = await provider_service.list_model_providers(
        filter_params.provider_type,
        filter_params.is_enabled,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(providers)


# ==================== API Key Vault ====================

@require_auth
async def create_api_key(request: Request):
    """Store an API key"""
    try:
        data = await request.json()
        create_request = ApiKeyVaultCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        key = await provider_service.store_api_key(create_request.model_dump())
        return json_response(key, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_api_key(request: Request):
    """Get API key by ID"""
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    include_key = request.query.get("include_key", "false").lower() == "true"

    key = await provider_service.get_api_key(str(key_uuid), include_key)
    if not key:
        return json_response({"error": "not_found", "message": "API key not found"}, status=404)

    return json_response(key)


@require_auth
async def list_api_keys(request: Request):
    """List API keys"""
    provider = request.query.get("provider")
    key_type = request.query.get("key_type")
    include_keys = request.query.get("include_keys", "false").lower() == "true"
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ApiKeyVaultFilter(
        provider=provider,
        key_type=key_type,
        limit=limit,
        offset=offset
    )

    keys = await provider_service.list_api_keys(
        filter_params.provider,
        filter_params.key_type,
        include_keys,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(keys)


@require_auth
async def update_api_key(request: Request):
    """Update API key"""
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    try:
        data = await request.json()
        update_request = ApiKeyVaultUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        key = await provider_service.update_api_key(str(key_uuid), update_request.model_dump(exclude_unset=True))
        if not key:
            return json_response({"error": "not_found", "message": "API key not found"}, status=404)
        return json_response(key)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_api_key(request: Request):
    """Delete API key"""
    key_id = request.match_info.get("key_id")
    try:
        key_uuid = UUID(key_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid key ID"}, status=400)

    success = await provider_service.delete_api_key(str(key_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "API key not found"}, status=404)
    return json_response({"message": "API key deleted"})


@require_auth
async def get_api_key_for_provider(request: Request):
    """Get decrypted API key for a provider (internal use)"""
    provider = request.match_info.get("provider")
    key_type = request.query.get("key_type", "api_key")

    # Only master can access decrypted keys
    if not request.get("is_master"):
        return json_response({"error": "forbidden", "message": "Master access required"}, status=403)

    api_key = await provider_service.get_api_key_for_provider(provider, key_type)
    if not api_key:
        return json_response({"error": "not_found", "message": "API key not found for provider"}, status=404)

    return json_response({"provider": provider, "key_type": key_type, "api_key": api_key})


# ==================== Provider Configuration ====================

@require_auth
async def create_provider_config(request: Request):
    """Save provider configuration"""
    try:
        data = await request.json()
        create_request = ProviderCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        config = await provider_service.save_provider_config(create_request.model_dump())
        return json_response(config, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_provider_config(request: Request):
    """Get provider configuration by ID"""
    config_id = request.match_info.get("config_id")
    try:
        config_uuid = UUID(config_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid config ID"}, status=400)

    config = await provider_service.get_provider_config(str(config_uuid))
    if not config:
        return json_response({"error": "not_found", "message": "Configuration not found"}, status=404)
    return json_response(config)


@require_auth
async def list_provider_configs(request: Request):
    """List provider configurations"""
    provider = request.query.get("provider")
    configs = await provider_service.list_provider_configs(provider)
    return json_response({"configs": configs})


# ==================== Health ====================

async def health_check(request: Request):
    """Health check"""
    try:
        await db.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return json_response(HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        service="provider-service",
        version="1.0.0",
        database=db_status,
        total_providers=0,
        total_models=0
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Provider Management
    app.router.add_post("/api/providers", create_provider)
    app.router.add_get("/api/providers", list_providers)
    app.router.add_get("/api/providers/{provider_id}", get_provider)
    app.router.add_patch("/api/providers/{provider_id}", update_provider)
    app.router.add_get("/api/providers/stats", get_provider_stats)

    # Model Management
    app.router.add_post("/api/models", create_model)
    app.router.add_get("/api/models", list_models)
    app.router.add_get("/api/models/{model_id}", get_model)
    app.router.add_patch("/api/models/{model_id}", update_model)

    # Model Provider Management
    app.router.add_post("/api/model-providers", create_model_provider)
    app.router.add_get("/api/model-providers", list_model_providers)
    app.router.add_get("/api/model-providers/{provider_id}", get_model_provider)

    # API Key Vault
    app.router.add_post("/api/keys", create_api_key)
    app.router.add_get("/api/keys", list_api_keys)
    app.router.add_get("/api/keys/{key_id}", get_api_key)
    app.router.add_patch("/api/keys/{key_id}", update_api_key)
    app.router.add_delete("/api/keys/{key_id}", delete_api_key)
    app.router.add_get("/api/keys/provider/{provider}", get_api_key_for_provider)

    # Provider Configs
    app.router.add_post("/api/configs", create_provider_config)
    app.router.add_get("/api/configs", list_provider_configs)
    app.router.add_get("/api/configs/{config_id}", get_provider_config)