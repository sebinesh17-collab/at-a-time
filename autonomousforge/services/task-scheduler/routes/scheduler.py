"""
Task Scheduler routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response

from ..services.scheduler import scheduler
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


# ==================== Task CRUD ====================

@require_auth
async def create_task(request: Request):
    """Create a new task"""
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    project_id = data.get("project_id")
    if not project_id:
        return json_response({"error": "validation_error", "message": "project_id required"}, status=400)

    task = await scheduler.create_task(project_id, data)
    return json_response(task, status=201)


@require_auth
async def get_task(request: Request):
    """Get task by ID"""
    task_id = request.match_info.get("task_id")
    task = await scheduler.get_task(task_id)
    if not task:
        return json_response({"error": "not_found", "message": "Task not found"}, status=404)
    return json_response(task)


@require_auth
async def list_tasks(request: Request):
    """List tasks with filters"""
    project_id = request.query.get("project_id")
    status = request.query.get("status")
    limit = min(int(request.query.get("limit", 100)), 500)
    offset = int(request.query.get("offset", 0))

    tasks = await scheduler.list_tasks(project_id, status, limit, offset)
    total = await db.fetchval("SELECT COUNT(*) FROM tasks" + (" WHERE project_id = $1" if project_id else ""), *( [project_id] if project_id else []))

    return json_response({
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@require_auth
async def update_task(request: Request):
    """Update task"""
    task_id = request.match_info.get("task_id")
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    task = await scheduler.update_task(task_id, data)
    if not task:
        return json_response({"error": "not_found", "message": "Task not found"}, status=404)
    return json_response(task)


@require_auth
async def cancel_task(request: Request):
    """Cancel a task"""
    task_id = request.match_info.get("task_id")
    success = await scheduler.cancel_task(task_id)
    if not success:
        return json_response({"error": "not_found", "message": "Task not found or cannot be cancelled"}, status=404)
    return json_response({"message": "Task cancelled", "task_id": task_id})


# ==================== Task Hierarchy ====================

@require_auth
async def get_task_tree(request: Request):
    """Get full task hierarchy for a project"""
    project_id = request.match_info.get("project_id")
    tree = await scheduler.get_task_tree(project_id)
    return json_response(tree)


@require_auth
async def decompose_project(request: Request):
    """Decompose a project into hierarchical tasks"""
    project_id = request.match_info.get("project_id")
    try:
        data = await request.json()
    except:
        return json_response({"error": "validation_error", "message": "Invalid JSON"}, status=400)

    description = data.get("description", "")
    epic_titles = data.get("epic_titles")

    tasks = await scheduler.decompose_project(project_id, description, epic_titles)
    return json_response({"tasks": tasks, "count": len(tasks)})


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
        "service": "task-scheduler",
        "version": "1.0.0",
        "database": db_status,
        "scheduler_running": scheduler.running,
    })


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Tasks
    app.router.add_post("/api/tasks", create_task)
    app.router.add_get("/api/tasks", list_tasks)
    app.router.add_get("/api/tasks/{task_id}", get_task)
    app.router.add_put("/api/tasks/{task_id}", update_task)
    app.router.add_post("/api/tasks/{task_id}/cancel", cancel_task)

    # Task Hierarchy
    app.router.add_get("/api/projects/{project_id}/tasks/tree", get_task_tree)
    app.router.add_post("/api/projects/{project_id}/tasks/decompose", decompose_project)