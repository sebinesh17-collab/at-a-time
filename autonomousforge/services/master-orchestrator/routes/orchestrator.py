"""
Master Orchestrator routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from uuid import UUID
import json

from ..services.orchestrator import orchestrator
from ..database import db
from ..config import settings


def require_auth(handler):
    """Decorator to require authentication"""
    async def wrapper(request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return json_response({"error": "unauthorized", "message": "Missing or invalid authorization header"}, status=401)

        token = auth_header[7:]
        # Check master key
        if token.startswith("af_master_"):
            # Verify with auth service
            pass  # In production, verify with auth service
            request["owner_id"] = "master"
            request["is_master"] = True
            return await handler(request)

        # For now, extract owner_id from token (simplified)
        # In production, validate with auth service
        request["owner_id"] = UUID("00000000-0000-0000-0000-000000000001")  # Placeholder
        request["is_master"] = False
        return await handler(request)
    return wrapper


# ==================== Projects ====================

@require_auth
async def create_project(request: Request):
    """Create new project"""
    owner_id = request["owner_id"]
    try:
        data = await request.json()
        name = data.get("name")
        description = data.get("description", "")
        project_type = data.get("project_type")
        tech_stack = data.get("tech_stack", [])

        if not name or not project_type:
            return json_response({"error": "validation_error", "message": "Name and project_type required"}, status=400)

        result = await orchestrator.create_project(owner_id, name, description, project_type, tech_stack)
        return json_response(result, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=400)


@require_auth
async def list_projects(request: Request):
    """List projects"""
    owner_id = request["owner_id"]
    status = request.query.get("status")
    projects = await orchestrator.list_projects(owner_id, status)
    return json_response(projects)


@require_auth
async def get_project(request: Request):
    """Get project details"""
    owner_id = request["owner_id"]
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    project = await orchestrator.get_project(project_uuid, owner_id)
    if not project:
        return json_response({"error": "not_found", "message": "Project not found"}, status=404)

    return json_response(project)


@require_auth
async def update_project(request: Request):
    """Update project"""
    owner_id = request["owner_id"]
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    updates = []
    params = [project_uuid, owner_id]
    param_idx = 3

    for field in ["name", "description", "project_type", "tech_stack", "status", "repository_url", "branch_name", "deployment_url"]:
        if field in data:
            updates.append(f"{field} = ${param_idx}")
            params.append(data[field])
            param_idx += 1

    if not updates:
        return json_response({"error": "validation_error", "message": "No fields to update"}, status=400)

    updates.append("updated_at = NOW()")
    query = f"UPDATE projects SET {', '.join(updates)} WHERE id = $1 AND owner_id = $2"
    await db.execute(query, *params)

    project = await orchestrator.get_project(project_uuid, owner_id)
    return json_response(project)


@require_auth
async def delete_project(request: Request):
    """Delete project"""
    owner_id = request["owner_id"]
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    result = await db.execute("DELETE FROM projects WHERE id = $1 AND owner_id = $2", project_uuid, owner_id)
    if result == "DELETE 0":
        return json_response({"error": "not_found", "message": "Project not found"}, status=404)

    return json_response({"message": "Project deleted"})


# ==================== Tasks ====================

@require_auth
async def get_task_tree(request: Request):
    """Get task hierarchy for project"""
    owner_id = request["owner_id"]
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    # Verify project ownership
    project = await orchestrator.get_project(project_uuid, owner_id)
    if not project:
        return json_response({"error": "not_found", "message": "Project not found"}, status=404)

    tasks = await orchestrator.get_task_tree(project_uuid)
    return json_response(tasks)


@require_auth
async def decompose_project(request: Request):
    """Decompose project into tasks"""
    owner_id = request["owner_id"]
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    try:
        data = await request.json()
        requirements = data.get("requirements", "")
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    # Verify project ownership
    project = await orchestrator.get_project(project_uuid, owner_id)
    if not project:
        return json_response({"error": "not_found", "message": "Project not found"}, status=404)

    tasks = await orchestrator.decompose_project(project_uuid, owner_id, requirements)
    return json_response({"tasks": tasks})


@require_auth
async def get_task(request: Request):
    """Get single task"""
    owner_id = request["owner_id"]
    task_id = request.match_info.get("task_id")
    try:
        task_uuid = UUID(task_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid task ID"}, status=400)

    row = await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_uuid)
    if not row:
        return json_response({"error": "not_found", "message": "Task not found"}, status=404)

    # Verify project ownership
    project = await orchestrator.get_project(row["project_id"], owner_id)
    if not project:
        return json_response({"error": "forbidden", "message": "Access denied"}, status=403)

    return json_response(dict(row))


@require_auth
async def execute_task(request: Request):
    """Execute a task"""
    owner_id = request["owner_id"]
    task_id = request.match_info.get("task_id")
    try:
        task_uuid = UUID(task_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid task ID"}, status=400)

    try:
        data = await request.json()
        agent_id = data.get("agent_id")
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    if not agent_id:
        return json_response({"error": "validation_error", "message": "agent_id required"}, status=400)

    # Verify task exists and belongs to owner's project
    task = await db.fetchrow("SELECT * FROM tasks WHERE id = $1", task_uuid)
    if not task:
        return json_response({"error": "not_found", "message": "Task not found"}, status=404)

    project = await orchestrator.get_project(task["project_id"], owner_id)
    if not project:
        return json_response({"error": "forbidden", "message": "Access denied"}, status=403)

    result = await orchestrator.execute_task(task_uuid, agent_id)
    return json_response(result)


@require_auth
async def list_available_agents(request: Request):
    """List available agents for task assignment"""
    level = request.query.get("level")
    department = request.query.get("department")

    agents = await orchestrator.get_available_agents(
        level=int(level) if level else None,
        department=department
    )
    return json_response(agents)


# ==================== Agent Communication ====================

@require_auth
async def send_agent_message(request: Request):
    """Send message between agents"""
    owner_id = request["owner_id"]
    try:
        data = await request.json()
        project_id = UUID(data.get("project_id"))
        task_id = UUID(data.get("task_id")) if data.get("task_id") else None
        sender_id = data.get("sender_id")
        recipient_id = data.get("recipient_id")
        message_type = data.get("message_type")
        content = data.get("content", {})
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    if not all([project_id, sender_id, recipient_id, message_type]):
        return json_response({"error": "validation_error", "message": "Missing required fields"}, status=400)

    # Verify project ownership
    project = await orchestrator.get_project(project_id, owner_id)
    if not project:
        return json_response({"error": "forbidden", "message": "Access denied"}, status=403)

    msg_id = await orchestrator.send_agent_message(
        project_id, task_id, sender_id, recipient_id, message_type, content
    )
    return json_response({"message_id": str(msg_id)})


@require_auth
async def get_task_messages(request: Request):
    """Get messages for a task"""
    owner_id = request["owner_id"]
    task_id = request.match_info.get("task_id")
    try:
        task_uuid = UUID(task_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid task ID"}, status=400)

    # Verify task belongs to owner's project
    task = await db.fetchrow("SELECT project_id FROM tasks WHERE id = $1", task_uuid)
    if not task:
        return json_response({"error": "not_found", "message": "Task not found"}, status=404)

    project = await orchestrator.get_project(task["project_id"], owner_id)
    if not project:
        return json_response({"error": "forbidden", "message": "Access denied"}, status=403)

    rows = await db.fetch("""
        SELECT * FROM messages WHERE task_id = $1 ORDER BY timestamp
    """, task_uuid)
    return json_response([dict(row) for row in rows])


# ==================== Model Integration ====================

@require_auth
async def call_model(request: Request):
    """Call model through gateway"""
    try:
        data = await request.json()
        model_id = data.get("model")
        prompt = data.get("prompt")
        context = data.get("context", {})
        tools = data.get("tools", [])
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    if not model_id or not prompt:
        return json_response({"error": "validation_error", "message": "model and prompt required"}, status=400)

    result = await orchestrator.call_model(model_id, prompt, context, tools)
    return json_response(result)


# ==================== Monitoring ====================

async def get_stats(request: Request):
    """Get system statistics"""
    stats = await orchestrator.get_system_stats()
    return json_response(stats)


async def health_check(request: Request):
    """Health check"""
    try:
        await db.fetchval("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    return json_response({
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "master-orchestrator",
        "version": "1.0.0",
        "database": db_status,
    })


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/orchestrator/stats", get_stats)

    # Projects
    app.router.add_post("/api/orchestrator/projects", create_project)
    app.router.add_get("/api/orchestrator/projects", list_projects)
    app.router.add_get("/api/orchestrator/projects/{project_id}", get_project)
    app.router.add_put("/api/orchestrator/projects/{project_id}", update_project)
    app.router.add_delete("/api/orchestrator/projects/{project_id}", delete_project)

    # Tasks
    app.router.add_get("/api/orchestrator/projects/{project_id}/tasks", get_task_tree)
    app.router.add_post("/api/orchestrator/projects/{project_id}/decompose", decompose_project)
    app.router.add_get("/api/orchestrator/tasks/{task_id}", get_task)
    app.router.add_post("/api/orchestrator/tasks/{task_id}/execute", execute_task)
    app.router.add_get("/api/orchestrator/agents/available", list_available_agents)

    # Agent Communication
    app.router.add_post("/api/orchestrator/messages", send_agent_message)
    app.router.add_get("/api/orchestrator/tasks/{task_id}/messages", get_task_messages)

    # Model
    app.router.add_post("/api/orchestrator/models/call", call_model)