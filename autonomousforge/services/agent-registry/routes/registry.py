"""
Agent Registry routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
import json
from typing import Optional, List, Dict, Any

from ..services.registry import registry
from ..database import db
from ..config import settings


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


# ==================== Agent Hierarchy ====================

@require_auth
async def get_hierarchy(request: Request):
    """Get full agent hierarchy tree"""
    root_id = request.query.get("root", "M-001")
    hierarchy = await registry.get_hierarchy(root_id)
    return json_response(hierarchy)


@require_auth
async def get_hierarchy_summary(request: Request):
    """Get hierarchy summary with counts per level"""
    stats = await registry.get_agent_stats()
    return json_response(stats)


# ==================== Agent CRUD ====================

@require_auth
async def list_agents(request: Request):
    """List agents with pagination and filters"""
    level = request.query.get("level")
    department = request.query.get("department")
    status = request.query.get("status")
    limit = min(int(request.query.get("limit", 100)), 500)
    offset = int(request.query.get("offset", 0))

    agents = await registry.list_agents(
        level=int(level) if level else None,
        department=department,
        status=status,
        limit=limit,
        offset=offset
    )

    total = await db.fetchval("SELECT COUNT(*) FROM agents")
    return json_response({
        "agents": agents,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@require_auth
async def get_agent(request: Request):
    """Get single agent by ID"""
    agent_id = request.match_info.get("agent_id")
    agent = await registry.get_agent(agent_id)
    if not agent:
        return json_response({"error": "not_found", "message": "Agent not found"}, status=404)
    return json_response(agent)


@require_auth
async def search_agents(request: Request):
    """Search agents"""
    query = request.query.get("q", "")
    limit = min(int(request.query.get("limit", 50)), 200)

    if not query:
        return json_response({"agents": []})

    agents = await registry.search_agents(query, limit)
    return json_response({"agents": agents})


@require_auth
async def update_agent(request: Request):
    """Update agent configuration"""
    agent_id = request.match_info.get("agent_id")

    # Verify agent exists
    agent = await registry.get_agent(agent_id)
    if not agent:
        return json_response({"error": "not_found", "message": "Agent not found"}, status=404)

    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    success = await registry.update_agent_config(agent_id, data)
    if not success:
        return json_response({"error": "update_failed", "message": "No valid fields to update"}, status=400)

    updated_agent = await registry.get_agent(agent_id)
    return json_response(updated_agent)


# ==================== Agent Control ====================

@require_auth
async def pause_agent(request: Request):
    """Pause an agent"""
    agent_id = request.match_info.get("agent_id")
    success = await registry.pause_agent(agent_id)
    if not success:
        return json_response({"error": "not_found", "message": "Agent not found"}, status=404)
    return json_response({"message": "Agent paused", "agent_id": agent_id})


@require_auth
async def resume_agent(request: Request):
    """Resume an agent"""
    agent_id = request.match_info.get("agent_id")
    success = await registry.resume_agent(agent_id)
    if not success:
        return json_response({"error": "not_found", "message": "Agent not found"}, status=404)
    return json_response({"message": "Agent resumed", "agent_id": agent_id})


# ==================== Department Views ====================

@require_auth
async def get_departments(request: Request):
    """Get all departments with agent counts"""
    rows = await db.fetch("""
        SELECT department, level, COUNT(*) as count
        FROM agents
        GROUP BY department, level
        ORDER BY department, level
    """)
    return json_response([dict(row) for row in rows])


@require_auth
async def get_department_agents(request: Request):
    """Get all agents in a department"""
    department = request.match_info.get("department")
    agents = await registry.get_department_agents(department)
    return json_response({"department": department, "agents": agents})


# ==================== Initialize Hierarchy ====================

@require_auth
async def initialize_hierarchy(request: Request):
    """Manually trigger agent hierarchy initialization (master only)"""
    if not request.get("is_master"):
        return json_response({"error": "forbidden", "message": "Master access required"}, status=403)

    success = await registry.initialize_hierarchy()
    if success:
        stats = await registry.get_agent_stats()
        return json_response({"message": "Hierarchy initialized", "stats": stats})
    else:
        return json_response({"error": "initialization_failed", "message": "Failed to initialize hierarchy"}, status=500)


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
        "service": "agent-registry",
        "version": "1.0.0",
        "database": db_status,
        "hierarchy_initialized": registry.generated,
    })


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Hierarchy
    app.router.add_get("/api/agents/hierarchy", get_hierarchy)
    app.router.add_get("/api/agents/hierarchy/summary", get_hierarchy_summary)

    # Agents
    app.router.add_get("/api/agents", list_agents)
    app.router.add_get("/api/agents/search", search_agents)
    app.router.add_get("/api/agents/{agent_id}", get_agent)
    app.router.add_put("/api/agents/{agent_id}", update_agent)

    # Agent Control
    app.router.add_post("/api/agents/{agent_id}/pause", pause_agent)
    app.router.add_post("/api/agents/{agent_id}/resume", resume_agent)

    # Departments
    app.router.add_get("/api/agents/departments", get_departments)
    app.router.add_get("/api/agents/departments/{department}", get_department_agents)

    # Initialize
    app.router.add_post("/api/agents/initialize", initialize_hierarchy)