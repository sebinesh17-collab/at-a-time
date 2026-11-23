"""
Knowledge Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID

from ..services.knowledge import knowledge_service
from ..database import db
from ..models.schemas import (
    KnowledgeChunkCreate, KnowledgeChunkUpdate, KnowledgeChunkResponse,
    KnowledgeSearchRequest, KnowledgeSearchResult, KnowledgeSearchResponse,
    KnowledgeIngestRequest, KnowledgeIngestResponse,
    HealthResponse
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


# ==================== Chunks ====================

@require_auth
async def create_chunk(request: Request):
    """Create a knowledge chunk"""
    try:
        data = await request.json()
        create_request = KnowledgeChunkCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        chunk = await knowledge_service.create_chunk(create_request.model_dump())
        return json_response(chunk, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_chunk(request: Request):
    """Get chunk by ID"""
    chunk_id = request.match_info.get("chunk_id")
    try:
        chunk_uuid = UUID(chunk_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid chunk ID"}, status=400)

    chunk = await knowledge_service.get_chunk(str(chunk_uuid))
    if not chunk:
        return json_response({"error": "not_found", "message": "Chunk not found"}, status=404)
    return json_response(chunk)


@require_auth
async def update_chunk(request: Request):
    """Update chunk"""
    chunk_id = request.match_info.get("chunk_id")
    try:
        chunk_uuid = UUID(chunk_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid chunk ID"}, status=400)

    try:
        data = await request.json()
        update_request = KnowledgeChunkUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        chunk = await knowledge_service.update_chunk(str(chunk_uuid), update_request.model_dump(exclude_unset=True))
        if not chunk:
            return json_response({"error": "not_found", "message": "Chunk not found"}, status=404)
        return json_response(chunk)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_chunk(request: Request):
    """Delete chunk"""
    chunk_id = request.match_info.get("chunk_id")
    try:
        chunk_uuid = UUID(chunk_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid chunk ID"}, status=400)

    success = await knowledge_service.delete_chunk(str(chunk_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Chunk not found"}, status=404)
    return json_response({"message": "Chunk deleted"})


# ==================== Search ====================

@require_auth
async def search_chunks(request: Request):
    """Search knowledge chunks"""
    try:
        data = await request.json()
        search_request = KnowledgeSearchRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    results = await knowledge_service.search_chunks(
        search_request.project_id,
        search_request.query,
        search_request.top_k,
        search_request.threshold,
        [str(fid) for fid in search_request.file_ids] if search_request.file_ids else None,
        search_request.metadata_filter
    )

    response = KnowledgeSearchResponse(
        results=results,
        total_found=len(results),
        query_time_ms=0  # Would need to track this
    )
    return json_response(response.model_dump())


# ==================== Ingestion ====================

@require_auth
async def ingest_knowledge(request: Request):
    """Ingest knowledge from files"""
    try:
        data = await request.json()
        ingest_request = KnowledgeIngestRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await knowledge_service.ingest_knowledge(
            ingest_request.project_id,
            [str(fid) for fid in ingest_request.file_ids] if ingest_request.file_ids else None,
            ingest_request.chunk_size,
            ingest_request.chunk_overlap,
            ingest_request.generate_embeddings,
            ingest_request.embedding_model
        )
        return json_response(result)
    except Exception as e:
        return json_response({"error": "ingestion_failed", "message": str(e)}, status=500)


# ==================== Health ====================

async def health_check(request: Request):
    """Health check endpoint"""
    return json_response(HealthResponse(
        status="healthy",
        service="knowledge-service",
        version="1.0.0",
        database="healthy"
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Chunks
    app.router.add_post("/api/knowledge/chunks", create_chunk)
    app.router.add_get("/api/knowledge/chunks/{chunk_id}", get_chunk)
    app.router.add_patch("/api/knowledge/chunks/{chunk_id}", update_chunk)
    app.router.add_delete("/api/knowledge/chunks/{chunk_id}", delete_chunk)

    # Search
    app.router.add_post("/api/knowledge/search", search_chunks)

    # Ingestion
    app.router.add_post("/api/knowledge/ingest", ingest_knowledge)