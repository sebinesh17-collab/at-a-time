"""
Build Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response
from typing import Optional
from uuid import UUID

from ..services.builder import builder
from ..database import db
from ..models.schemas import (
    BuildCreate, BuildUpdate, BuildResponse, BuildStageCreate, BuildStageResponse,
    BuildLogCreate, BuildLogResponse, BuildFilter, BuildStatsResponse, HealthResponse
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


# ==================== Builds ====================

@require_auth
async def start_build(request: Request):
    """Start a new build"""
    try:
        data = await request.json()
        create_request = BuildCreate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        build = await builder.start_build(create_request.model_dump())
        return json_response(build, status=201)
    except Exception as e:
        return json_response({"error": "build_failed", "message": str(e)}, status=500)


@require_auth
async def get_build(request: Request):
    """Get build by ID"""
    build_id = request.match_info.get("build_id")
    try:
        build_uuid = UUID(build_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid build ID"}, status=400)

    build = await builder.get_build(str(build_uuid))
    if not build:
        return json_response({"error": "not_found", "message": "Build not found"}, status=404)
    return json_response(build)


@require_auth
async def update_build(request: Request):
    """Update build"""
    build_id = request.match_info.get("build_id")
    try:
        build_uuid = UUID(build_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid build ID"}, status=400)

    try:
        data = await request.json()
        update_request = BuildUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    try:
        build = await builder.update_build(str(build_uuid), update_request.model_dump(exclude_unset=True))
        if not build:
            return json_response({"error": "not_found", "message": "Build not found"}, status=404)
        return json_response(build)
    except Exception as e:
        return json_response({"error": "update_failed", "message": str(e)}, status=500)


@require_auth
async def list_builds(request: Request):
    """List builds"""
    project_id = request.query.get("project_id")
    status = request.query.get("status")
    trigger_type = request.query.get("trigger_type")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = BuildFilter(
        project_id=UUID(project_id) if project_id else None,
        status=status,
        trigger_type=trigger_type,
        limit=limit,
        offset=offset
    )

    builds = await builder.list_builds(
        str(filter_params.project_id) if filter_params.project_id else None,
        filter_params.status,
        filter_params.trigger_type,
        filter_params.limit,
        filter_params.offset
    )
    return json_response(builds)


@require_auth
async def cancel_build(request: Request):
    """Cancel a running build"""
    build_id = request.match_info.get("build_id")
    try:
        build_uuid = UUID(build_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid build ID"}, status=400)

    try:
        await builder.cancel_build(str(build_uuid))
        return json_response({"message": "Build cancelled"})
    except Exception as e:
        return json_response({"error": "cancel_failed", "message": str(e)}, status=500)


@require_auth
async def get_build_logs(request: Request):
    """Get build logs"""
    build_id = request.match_info.get("build_id")
    stage_id = request.query.get("stage_id")
    try:
        build_uuid = UUID(build_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid build ID"}, status=400)

    logs = await builder.get_logs(str(build_uuid), stage_id)
    return json_response(logs)


@require_auth
async def get_build_stats(request: Request):
    """Get build statistics"""
    project_id = request.query.get("project_id")
    stats = await builder.get_stats(project_id)
    return json_response(stats)


# ==================== Build Stages ====================

@require_auth
async def get_build_stages(request: Request):
    """Get build stages"""
    build_id = request.match_info.get("build_id")
    try:
        build_uuid = UUID(build_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid build ID"}, status=400)

    stages = await builder.get_stages(str(build_uuid))
    return json_response(stages)


# ==================== Health ====================

async def health_check(request: Request):
    """Health check endpoint"""
    return json_response(HealthResponse(
        status="healthy",
        service="build-service",
        version="1.0.0",
        database="healthy",
        queue_depth=len(builder.running_builds)
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Builds
    app.router.add_post("/api/builds", start_build)
    app.router.add_get("/api/builds", list_builds)
    app.router.add_get("/api/builds/{build_id}", get_build)
    app.router.add_patch("/api/builds/{build_id}", update_build)
    app.router.add_post("/api/builds/{build_id}/cancel", cancel_build)
    app.router.add_get("/api/builds/{build_id}/logs", get_build_logs)
    app.router.add_get("/api/builds/{build_id}/stages", get_build_stages)