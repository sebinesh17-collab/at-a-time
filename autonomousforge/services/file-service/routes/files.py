"""
File Service routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response, Response
from typing import Optional
from uuid import UUID

from ..services.files import file_service
from ..database import db
from ..models.schemas import (
    FileCreate, FileUpdate, FileResponse, FileUploadResponse, FileProcessRequest,
    FileProcessResponse, DirectoryCreate, DirectoryResponse, FileSearchRequest, FileSearchResponse,
    FileFilter, DirectoryFilter, ProjectFileTreeResponse, FileStatsResponse, HealthResponse
)
import io


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


# ==================== File Operations ====================

@require_auth
async def upload_file(request: Request):
    """Upload a file"""
    try:
        reader = await request.multipart()
        file_field = None
        filename = None
        content_type = None
        metadata = {}
        project_id = None

        async for field in reader:
            if field.name == "file":
                file_field = field
                filename = field.filename
                content_type = field.headers.get("Content-Type")
            elif field.name == "metadata":
                import json
                metadata = json.loads(await field.text())
            elif field.name == "project_id":
                project_id = await field.text()

        if not file_field:
            return json_response({"error": "validation_error", "message": "No file provided"}, status=400)

        # Read file content
        file_content = await file_field.read()
        size_bytes = len(file_content)

        # Create file metadata using schema
        file_data = FileCreate(
            project_id=UUID(project_id) if project_id else None,
            filename=filename,
            original_filename=filename,
            mime_type=content_type or "application/octet-stream",
            size_bytes=size_bytes,
            storage_path=f"{project_id or 'global'}/{filename}",
            storage_provider="local",
            metadata=metadata
        )

        file_obj = io.BytesIO(file_content)
        file_meta = await file_service.upload_file(
            file_obj, filename, content_type, metadata, project_id, request["owner_id"]
        )
        return json_response(file_meta, status=201)

    except Exception as e:
        return json_response({"error": "upload_failed", "message": str(e)}, status=500)


@require_auth
async def get_file(request: Request):
    """Get file metadata"""
    file_id = request.match_info.get("file_id")
    try:
        file_uuid = UUID(file_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid file ID"}, status=400)

    file_meta = await file_service.get_file(str(file_uuid))
    if not file_meta:
        return json_response({"error": "not_found", "message": "File not found"}, status=404)
    return json_response(file_meta)


@require_auth
async def download_file(request: Request):
    """Download file content"""
    file_id = request.match_info.get("file_id")
    try:
        file_uuid = UUID(file_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid file ID"}, status=400)

    result = await file_service.download_file(str(file_uuid))
    if not result:
        return json_response({"error": "not_found", "message": "File not found"}, status=404)

    content, filename, content_type = result
    return Response(
        body=content,
        headers={
            "Content-Type": content_type,
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@require_auth
async def list_files(request: Request):
    """List files"""
    project_id = request.query.get("project_id")
    limit = min(int(request.query.get("limit", 50)), 500)
    offset = int(request.query.get("offset", 0))

    filter_params = FileFilter(
        project_id=UUID(project_id) if project_id else None,
        owner_id=UUID(request["owner_id"]) if request["owner_id"] != "master" else None,
        limit=limit,
        offset=offset
    )

    files = await file_service.list_files(
        str(filter_params.project_id) if filter_params.project_id else None,
        request["owner_id"],
        filter_params.limit,
        filter_params.offset
    )
    total = await db.fetchval(
        "SELECT COUNT(*) FROM files WHERE project_id = $1 AND owner_id = $2" if project_id else "SELECT COUNT(*) FROM files WHERE owner_id = $1",
        project_id or request["owner_id"],
        request["owner_id"]
    )

    return json_response({
        "files": files,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@require_auth
async def update_file(request: Request):
    """Update file metadata"""
    file_id = request.match_info.get("file_id")
    try:
        file_uuid = UUID(file_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid file ID"}, status=400)

    try:
        data = await request.json()
        update_request = FileUpdate(**data)
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    file_meta = await file_service.update_file(str(file_uuid), update_request.model_dump(exclude_unset=True))
    if not file_meta:
        return json_response({"error": "not_found", "message": "File not found"}, status=404)
    return json_response(file_meta)


@require_auth
async def delete_file(request: Request):
    """Delete a file"""
    file_id = request.match_info.get("file_id")
    try:
        file_uuid = UUID(file_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid file ID"}, status=400)

    success = await file_service.delete_file(str(file_uuid))
    if not success:
        return json_response({"error": "not_found", "message": "File not found"}, status=404)
    return json_response({"message": "File deleted"})


@require_auth
async def search_files(request: Request):
    """Search files"""
    query = request.query.get("q", "")
    project_id = request.query.get("project_id")
    limit = min(int(request.query.get("limit", 50)), 200)

    if not query:
        return json_response({"files": []})

    files = await file_service.search_files(query, project_id, limit)
    return json_response({"files": files})


# ==================== Directory Operations ====================

@require_auth
async def create_directory(request: Request):
    """Create a directory"""
    try:
        data = await request.json()
        create_request = DirectoryCreate(**data, owner_id=request["owner_id"])
    except Exception as e:
        return json_response({"error": "validation_error", "message": str(e)}, status=400)

    directory = await file_service.create_directory(create_request.model_dump())
    return json_response(directory, status=201)


@require_auth
async def get_directory(request: Request):
    """Get directory"""
    dir_id = request.match_info.get("dir_id")
    try:
        dir_uuid = UUID(dir_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid directory ID"}, status=400)

    directory = await file_service.get_directory(str(dir_uuid))
    if not directory:
        return json_response({"error": "not_found", "message": "Directory not found"}, status=404)
    return json_response(directory)


@require_auth
async def list_directories(request: Request):
    """List directories"""
    parent_id = request.query.get("parent_id")
    project_id = request.query.get("project_id")

    filter_params = DirectoryFilter(
        parent_id=UUID(parent_id) if parent_id else None,
        project_id=UUID(project_id) if project_id else None,
        owner_id=UUID(request["owner_id"]) if request["owner_id"] != "master" else None
    )

    dirs = await file_service.list_directories(
        str(filter_params.parent_id) if filter_params.parent_id else None,
        str(filter_params.project_id) if filter_params.project_id else None
    )
    return json_response({"directories": dirs})


@require_auth
async def delete_directory(request: Request):
    """Delete directory"""
    dir_id = request.match_info.get("dir_id")
    try:
        dir_uuid = UUID(dir_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid directory ID"}, status=400)

    recursive = request.query.get("recursive", "false").lower() == "true"

    success = await file_service.delete_directory(str(dir_uuid), recursive)
    if not success:
        return json_response({"error": "not_found", "message": "Directory not found or not empty"}, status=404)
    return json_response({"message": "Directory deleted"})


# ==================== Project File Tree ====================

@require_auth
async def get_project_file_tree(request: Request):
    """Get project file tree"""
    project_id = request.match_info.get("project_id")
    try:
        project_uuid = UUID(project_id)
    except:
        return json_response({"error": "invalid_id", "message": "Invalid project ID"}, status=400)

    tree = await file_service.get_project_file_tree(str(project_uuid))
    return json_response(tree)


@require_auth
async def get_file_stats(request: Request):
    """Get file statistics"""
    project_id = request.query.get("project_id")
    stats = await file_service.get_stats(project_id)
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
        service="file-service",
        version="1.0.0",
        database=db_status,
        total_files=0,
        total_size_bytes=0
    ).model_dump())


# Route registration
def setup_routes(app: web.Application):
    app.router.add_get("/health", health_check)

    # Files
    app.router.add_post("/api/files", upload_file)
    app.router.add_get("/api/files", list_files)
    app.router.add_get("/api/files/search", search_files)
    app.router.add_get("/api/files/{file_id}", get_file)
    app.router.add_get("/api/files/{file_id}/download", download_file)
    app.router.add_patch("/api/files/{file_id}", update_file)
    app.router.add_delete("/api/files/{file_id}", delete_file)

    # Directories
    app.router.add_post("/api/directories", create_directory)
    app.router.add_get("/api/directories", list_directories)
    app.router.add_get("/api/directories/{dir_id}", get_directory)
    app.router.add_delete("/api/directories/{dir_id}", delete_directory)

    # Project Tree
    app.router.add_get("/api/projects/{project_id}/files/tree", get_project_file_tree)

    # Stats
    app.router.add_get("/api/files/stats", get_file_stats)