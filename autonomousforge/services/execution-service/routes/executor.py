"""
Execution Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID

from ..services.executor import executor
from ..database import db
from ..models.schemas import (
    ExecutionCreate, ExecutionUpdate, ExecutionResponse,
    SandboxCreate, SandboxUpdate, SandboxResponse, SandboxCommand, SandboxCommandResponse,
    ExecutionFilter, SandboxFilter, ExecutionStatsResponse, HealthResponse
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


# ==================== Executions ====================

@require_auth
async def execute_code(request: Request):
    """Execute code"""
    try:
        data = await request.json()
        create_request = ExecutionCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await executor.execute_code(create_request.model_dump())
        return json_response(result)
    except Exception as e:
        return json_response({"error": "execution_failed", "message": str(e)}, status=500)


@require_auth
async def get_execution(request: Request):
    """Get execution by ID"""
    execution_id = request.match_info.get("execution_id")
    try:
        execution_uuid = UUID(execution_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid execution ID"}, status=400)

    execution = await executor.get_execution(str(execution_uuid))
    if not execution:
        return json_response({"error": "not_found", "message": "Execution not found"}, status=404)
    return json_response(execution)


@require_auth
async def update_execution(request: Request):
    """Update execution"""
    execution_id = request.match_info.get("execution_id")
    try:
        execution_uuid = UUID(execution_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid execution ID"}, status=400)

    try:
        data = await request.json()
        update_request = ExecutionUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        execution = await executor.update_execution(str(execution_uuid), update_request.model_dump(exclude_unset=True))
        if not execution:
            return json_response({"error": "not_found", "message": "Execution not found"}, status=404)
        return json_response(execution)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_executions(request: Request):
    """List executions"""
    project_id = request.query.get("project_id")
    task_id = request.query.get("task_id")
    status = request.query.get("status")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = ExecutionFilter(
        project_id=UUID(project_id) if project_id else None,
        task_id=UUID(task_id) if task_id else None,
        status=status,
        limit=limit,
        offset=offset
    )

    executions = await executor.list_executions(
        str(filter_params.project_id) if filter_params.project_id else None,
        str(filter_params.task_id) if filter_params.task_id else None,
        filter_params.status,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(executions)


@require_auth
async def cancel_execution(request: Request):
    """Cancel execution"""
    execution_id = request.match_info.get("execution_id")
    try:
        execution_uuid = UUID(execution_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid execution ID"}, status=400)

    success = await executor.cancel_execution(str(execution_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Execution not found or not running"}, status=404)
    return json_response({"message": "Execution cancelled"})


# ==================== Sandboxes ====================

@require_auth
async def create_sandbox(request: Request):
    """Create a sandbox"""
    try:
        data = await request.json()
        create_request = SandboxCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        sandbox = await executor.create_sandbox(create_request.model_dump())
        return json_response(sandbox, status=201)
    except Exception as e:
        return json_response({"error": "creation_failed", "message": str(e)}, status=500)


@require_auth
async def get_sandbox(request: Request):
    """Get sandbox by ID"""
    sandbox_id = request.match_info.get("sandbox_id")
    try:
        sandbox_uuid = UUID(sandbox_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid sandbox ID"}, status=400)

    sandbox = await executor.get_sandbox(str(sandbox_uuid))
    if not sandbox:
        return json_response({"error": "not_found", "message": "Sandbox not found"}, status=404)
    return json_response(sandbox)


@require_auth
async def update_sandbox(request: Request):
    """Update sandbox"""
    sandbox_id = request.match_info.get("sandbox_id")
    try:
        sandbox_uuid = UUID(sandbox_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid sandbox ID"}, status=400)

    try:
        data = await request.json()
        update_request = SandboxUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        sandbox = await executor.update_sandbox(str(sandbox_uuid), update_request.model_dump(exclude_unset=True))
        if not sandbox:
            return json_response({"error": "not_found", "message": "Sandbox not found"}, status=404)
        return json_response(sandbox)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_sandboxes(request: Request):
    """List sandboxes"""
    project_id = request.query.get("project_id")
    status = request.query.get("status")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = SandboxFilter(
        project_id=UUID(project_id) if project_id else None,
        status=status,
        limit=limit,
        offset=offset
    )

    sandboxes = await executor.list_sandboxes(
        str(filter_params.project_id) if filter_params.project_id else None,
        filter_params.status,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(sandboxes)


@require_auth
async def destroy_sandbox(request: Request):
    """Destroy sandbox"""
    sandbox_id = request.match_info.get("sandbox_id")
    try:
        sandbox_uuid = UUID(sandbox_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid sandbox ID"}, status=400)

    success = await executor.destroy_sandbox(str(sandbox_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "Sandbox not found"}, status=404)
    return json_response({"message": "Sandbox destroyed"})


@require_auth
async def execute_sandbox_command(request: Request):
    """Execute command in sandbox"""
    sandbox_id = request.match_info.get("sandbox_id")
    try:
        sandbox_uuid = UUID(sandbox_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid sandbox ID"}, status=400)

    try:
        data = await request.json()
        command_request = SandboxCommand(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        result = await executor.execute_sandbox_command(str(sandbox_uuid), command_request.model_dump())
        return json_response(result)
    except Exception as e:
        return json_response({"error": "execution_failed", "message": str(e)}, status=500)


@require_auth
async def get_execution_stats(request: Request):
    """Get execution statistics"""
    project_id = request.query.get("project_id")
    stats = await executor.get_stats(project_id)
    return json_response(stats)


# ==================== Health ====================

async def health_check(request: Request):
    """Health check endpoint"""
    return json_response(HealthResponse(
        status="healthy",
        service="execution-service",
        version="1.0.0",
        database="healthy",
        active_containers=len(executor.running_executions)
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Executions
    app.router.add_post("/api/execute", execute_code)
    app.router.add_get("/api/executions", list_executions)
    app.router.add_get("/api/executions/{execution_id}", get_execution)
    app.router.add_patch("/api/executions/{execution_id}", update_execution)
    app.router.add_post("/api/executions/{execution_id}/cancel", cancel_execution)

    # Sandboxes
    app.router.add_post("/api/sandboxes", create_sandbox)
    app.router.add_get("/api/sandboxes", list_sandboxes)
    app.router.add_get("/api/sandboxes/{sandbox_id}", get_sandbox)
    app.router.add_patch("/api/sandboxes/{sandbox_id}", update_sandbox)
    app.router.add_delete("/api/sandboxes/{sandbox_id}", destroy_sandbox)
    app.router.add_post("/api/sandboxes/{sandbox_id}/execute", execute_sandbox_command)

    # Stats
    app.router.add_get("/api/executions/stats", get_execution_stats)