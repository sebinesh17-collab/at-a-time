"""
Memory Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID

from ..services.memory import memory_service
from ..database import db
from ..models.schemas import (
    MemoryCreate, MemoryUpdate, MemoryResponse,
    MemorySearchRequest, MemorySearchResponse,
    ConversationCreate, ConversationResponse,
    ConversationMessageCreate, ConversationMessageResponse,
    KnowledgeEntryCreate, KnowledgeEntryResponse,
    AgentStateCreate, AgentStateResponse,
    MemoryFilter, ConversationFilter, KnowledgeFilter, AgentStateFilter,
    MemoryStatsResponse, HealthResponse
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


# ==================== Memories ====================

@require_auth
async def create_memory(request: Request):
    """Create a memory entry"""
    try:
        data = await request.json()
        create_request = MemoryCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        memory = await memory_service.create_memory(create_request.model_dump())
        return json_response(memory, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_memory(request: Request):
    """Get memory by ID"""
    memory_id = request.match_info.get("memory_id")
    try:
        memory_uuid = UUID(memory_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid memory ID"}, status=400)

    memory = await memory_service.get_memory(str(memory_uuid))
    if not memory:
        return json_response({"error": "not_found", "message": "Memory not found"}, status=404)
    return json_response(memory)


@require_auth
async def update_memory(request: Request):
    """Update memory"""
    memory_id = request.match_info.get("memory_id")
    try:
        memory_uuid = UUID(memory_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid memory ID"}, status=400)

    try:
        data = await request.json()
        update_request = MemoryUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        memory = await memory_service.update_memory(str(memory_uuid), update_request.model_dump(exclude_unset=True))
        if not memory:
            return json_response({"error": "not_found", "message": "Memory not found"}, status=404)
        return json_response(memory)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def delete_memory(request: Request):
    """Delete memory"""
    memory_id = request.match_info.get("memory_id")
    try:
        memory_uuid = UUID(memory_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid memory ID"}, status=400)

    success = await memory_service.delete_memory(str(memory_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Memory not found"}, status=404)
    return json_response({"message": "Memory deleted"})


@require_auth
async def list_memories(request: Request):
    """List memories"""
    memory_type = request.query.get("memory_type")
    project_id = request.query.get("project_id")
    agent_id = request.query.get("agent_id")
    conversation_id = request.query.get("conversation_id")
    workflow_id = request.query.get("workflow_id")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = MemoryFilter(
        memory_type=memory_type,
        project_id=UUID(project_id) if project_id else None,
        agent_id=agent_id,
        conversation_id=UUID(conversation_id) if conversation_id else None,
        workflow_id=UUID(workflow_id) if workflow_id else None,
        limit=limit,
        offset=offset
    )

    memories = await memory_service.list_memories(
        filter_params.memory_type,
        str(filter_params.project_id) if filter_params.project_id else None,
        filter_params.agent_id,
        str(filter_params.conversation_id) if filter_params.conversation_id else None,
        str(filter_params.workflow_id) if filter_params.workflow_id else None,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(memories)


@require_auth
async def search_memories(request: Request):
    """Search memories"""
    try:
        data = await request.json()
        search_request = MemorySearchRequest(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    results = await memory_service.search_memories(
        search_request.memory_type,
        str(search_request.project_id) if search_request.project_id else None,
        search_request.agent_id,
        str(search_request.conversation_id) if search_request.conversation_id else None,
        str(search_request.workflow_id) if search_request.workflow_id else None,
        search_request.query,
        search_request.key_pattern,
        search_request.top_k,
        search_request.threshold,
        search_request.include_expired
    )

    response = MemorySearchResponse(
        results=results,
        total_found=len(results),
        query_time_ms=0
    )
    return json_response(response.model_dump())


# ==================== Conversations ====================

@require_auth
async def create_conversation(request: Request):
    """Create a conversation"""
    try:
        data = await request.json()
        create_request = ConversationCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        conversation = await memory_service.create_conversation(create_request.model_dump())
        return json_response(conversation, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_conversation(request: Request):
    """Get conversation by ID"""
    conversation_id = request.match_info.get("conversation_id")
    try:
        conv_uuid = UUID(conversation_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid conversation ID"}, status=400)

    conversation = await memory_service.get_conversation(str(conv_uuid))
    if not conversation:
        return json_response({"error": "not_found", "message": "Conversation not found"}, status=404)
    return json_response(conversation)


@require_auth
async def list_conversations(request: Request):
    """List conversations"""
    agent_id = request.query.get("agent_id")
    project_id = request.query.get("project_id")
    limit = min(int(request.query.get("limit", 50)), 200)
    offset = int(request.query.get("offset", 0))

    filter_params = ConversationFilter(
        agent_id=agent_id,
        project_id=UUID(project_id) if project_id else None,
        limit=limit,
        offset=offset
    )

    conversations = await memory_service.list_conversations(
        filter_params.agent_id,
        str(filter_params.project_id) if filter_params.project_id else None,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(conversations)


@require_auth
async def get_conversation_history(request: Request):
    """Get conversation history"""
    conversation_id = request.match_info.get("conversation_id")
    try:
        conv_uuid = UUID(conversation_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid conversation ID"}, status=400)

    limit = min(int(request.query.get("limit", 100)), 500)

    messages = await memory_service.get_conversation_history(str(conv_uuid), limit)
    return json_response({"messages": messages})


@require_auth
async def add_conversation_message(request: Request):
    """Add message to conversation"""
    conversation_id = request.match_info.get("conversation_id")
    try:
        conv_uuid = UUID(conversation_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid conversation ID"}, status=400)

    try:
        data = await request.json()
        message_request = ConversationMessageCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    message = await memory_service.add_conversation_message(str(conv_uuid), message_request.model_dump())
    return json_response(message, status=201)


# ==================== Knowledge Base ====================

@require_auth
async def add_knowledge(request: Request):
    """Add knowledge entry"""
    try:
        data = await request.json()
        create_request = KnowledgeEntryCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        knowledge = await memory_service.add_knowledge(create_request.model_dump())
        return json_response(knowledge, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_knowledge(request: Request):
    """Get knowledge by ID"""
    knowledge_id = request.match_info.get("knowledge_id")
    try:
        knowledge_uuid = UUID(knowledge_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid knowledge ID"}, status=400)

    knowledge = await memory_service.get_knowledge(str(knowledge_uuid))
    if not knowledge:
        return json_response({"error": "not_found", "message": "Knowledge not found"}, status=404)
    return json_response(knowledge)


@require_auth
async def search_knowledge(request: Request):
    """Search knowledge base"""
    query = request.query.get("q", "")
    project_id = request.query.get("project_id")
    tags = request.query.get("tags")
    limit = min(int(request.query.get("limit", 10)), 50)

    tag_list = tags.split(",") if tags else None
    knowledge = await memory_service.search_knowledge(query, project_id, tag_list, limit)
    return json_response({"knowledge": knowledge})


# ==================== Agent State ====================

@require_auth
async def save_agent_state(request: Request):
    """Save agent state"""
    agent_id = request.match_info.get("agent_id")
    try:
        data = await request.json()
        create_request = AgentStateCreate(**data, agent_id=agent_id)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    state = await memory_service.save_agent_state(agent_id, create_request.model_dump())
    return json_response(state)


@require_auth
async def get_agent_state(request: Request):
    """Get agent state"""
    agent_id = request.match_info.get("agent_id")
    state = await memory_service.get_agent_state(agent_id)
    if not state:
        return json_response({"error": "not_found", "message": "Agent state not found"}, status=404)
    return json_response(state)


@require_auth
async def delete_agent_state(request: Request):
    """Delete agent state"""
    agent_id = request.match_info.get("agent_id")
    success = await memory_service.delete_agent_state(agent_id)
    if not success:
        return json_response({"error": "not_found", "message": "Agent state not found"}, status=404)
    return json_response({"message": "Agent state deleted"})


@require_auth
async def get_memory_stats(request: Request):
    """Get memory statistics"""
    project_id = request.query.get("project_id")
    stats = await memory_service.get_stats(project_id)
    return json_response(stats)


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
        service="memory-service",
        version="1.0.0",
        database=db_status,
        total_memories=0,
        total_conversations=0
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Memories
    app.router.add_post("/api/memories", create_memory)
    app.router.add_get("/api/memories", list_memories)
    app.router.add_post("/api/memories/search", search_memories)
    app.router.add_get("/api/memories/{memory_id}", get_memory)
    app.router.add_patch("/api/memories/{memory_id}", update_memory)
    app.router.add_delete("/api/memories/{memory_id}", delete_memory)

    # Conversations
    app.router.add_post("/api/conversations", create_conversation)
    app.router.add_get("/api/conversations", list_conversations)
    app.router.add_get("/api/conversations/{conversation_id}", get_conversation)
    app.router.add_get("/api/conversations/{conversation_id}/messages", get_conversation_history)
    app.router.add_post("/api/conversations/{conversation_id}/messages", add_conversation_message)

    # Knowledge Base
    app.router.add_post("/api/knowledge", add_knowledge)
    app.router.add_get("/api/knowledge/{knowledge_id}", get_knowledge)
    app.router.add_get("/api/knowledge/search", search_knowledge)

    # Agent State
    app.router.add_post("/api/agents/{agent_id}/state", save_agent_state)
    app.router.add_get("/api/agents/{agent_id}/state", get_agent_state)
    app.router.add_delete("/api/agents/{agent_id}/state", delete_agent_state)

    # Stats
    app.router.add_get("/api/memories/stats", get_memory_stats)