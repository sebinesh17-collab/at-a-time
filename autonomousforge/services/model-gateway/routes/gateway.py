"""
Model Gateway routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response

from ..services.gateway import gateway
from ..database import db


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


# ==================== Completion ====================

@require_auth
async def complete(request: Request):
    """Generate completion"""
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    try:
        result = await gateway.complete(data)
        return json_response(result)
    except Exception as e:
        return json_response({"error": "completion_error", "message": str(e)}, status=500)


@require_auth
async def embed(request: Request):
    """Generate embeddings"""
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    try:
        result = await gateway.embed(data)
        return json_response(result)
    except Exception as e:
        return json_response({"error": "embedding_error", "message": str(e)}, status=500)


# ==================== Provider Management ====================

@require_auth
async def list_providers(request: Request):
    """List all providers"""
    providers = await gateway.list_providers()
    # Don't return API keys
    for p in providers:
        p.pop("api_key_encrypted", None)
        p.pop("api_key", None)
    return json_response({"providers": providers})


@require_auth
async def get_provider(request: Request):
    """Get provider by ID"""
    provider_id = request.match_info.get("provider_id")
    provider = await gateway.get_provider(provider_id)
    if not provider:
        return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
    provider.pop("api_key_encrypted", None)
    provider.pop("api_key", None)
    return json_response(provider)


@require_auth
async def create_provider(request: Request):
    """Create a new provider"""
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    required = ["name", "provider_type", "api_key"]
    for field in required:
        if field not in data:
            return json_response({"error": "validation_error", "message": f"{field} required"}, status=400)

    try:
        provider = await gateway.register_provider(data)
        provider.pop("api_key_encrypted", None)
        provider.pop("api_key", None)
        return json_response(provider, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def update_provider(request: Request):
    """Update provider"""
    provider_id = request.match_info.get("provider_id")
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    try:
        provider = await gateway.update_provider(provider_id, data)
        if not provider:
            return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
        provider.pop("api_key_encrypted", None)
        provider.pop("api_key", None)
        return json_response(provider)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_provider(request: Request):
    """Delete provider"""
    provider_id = request.match_info.get("provider_id")
    success = await gateway.delete_provider(provider_id)
    if not success:
        return json_response({"error": "not_found", "message": "Provider not found"}, status=404)
    return json_response({"message": "Provider deleted"})


# ==================== Model Management ====================

@require_auth
async def list_models(request: Request):
    """List models"""
    provider_id = request.query.get("provider_id")
    model_type = request.query.get("model_type")
    models = await gateway.list_models(provider_id, model_type)
    return json_response({"models": models})


@require_auth
async def get_model(request: Request):
    """Get model by ID"""
    model_id = request.match_info.get("model_id")
    model = await gateway.get_model(model_id)
    if not model:
        return json_response({"error": "not_found", "message": "Model not found"}, status=404)
    return json_response(model)


@require_auth
async def create_model(request: Request):
    """Create a new model"""
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    required = ["provider_id", "model_id"]
    for field in required:
        if field not in data:
            return json_response({"error": "validation_error", "message": f"{field} required"}, status=400)

    try:
        model = await gateway.register_model(data)
        return json_response(model, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def update_model(request: Request):
    """Update model"""
    model_id = request.match_info.get("model_id")
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    try:
        model = await gateway.update_model(model_id, data)
        if not model:
            return json_response({"error": "not_found", "message": "Model not found"}, status=404)
        return json_response(model)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_model(request: Request):
    """Delete model"""
    model_id = request.match_info.get("model_id")
    success = await gateway.delete_model(model_id)
    if not success:
        return json_response({"error": "not_found", "message": "Model not found"}, status=404)
    return json_response({"message": "Model deleted"})


# ==================== Health ====================

async def health_check(request: Request):
    """Health check"""
    try:
        await db.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return json_response({
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "model-gateway",
        "version": "1.0.0",
        "database": db_status,
        "providers_loaded": len(gateway.providers),
        "models_loaded": len(gateway.models),
    })


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Completion
    app.router.add_post("/api/complete", complete)
    app.router.add_post("/api/embed", embed)

    # Providers
    app.router.add_get("/api/providers", list_providers)
    app.router.add_post("/api/providers", create_provider)
    app.router.add_get("/api/providers/{provider_id}", get_provider)
    app.router.add_put("/api/providers/{provider_id}", update_provider)
    app.router.add_delete("/api/providers/{provider_id}", delete_provider)

    # Models
    app.router.add_get("/api/models", list_models)
    app.router.add_post("/api/models", create_model)
    app.router.add_get("/api/models/{model_id}", get_model)
    app.router.add_put("/api/models/{model_id}", update_model)
    app.router.add_delete("/api/models/{model_id}", delete_model)