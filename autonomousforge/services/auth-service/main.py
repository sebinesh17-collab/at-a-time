"""
Auth Service Main Entry Point
"""
from aiohttp import web
from aiohttp.web import middleware
from aiohttp_cors import setup as cors_setup, ResourceOptions
import asyncio
import logging

from .config import settings
from .database import db
from .services.auth_service import auth_service
from .routes.auth import (
    setup_owner, check_setup,
    login, login_2fa, logout, logout_all, refresh_token, get_me,
    change_password,
    get_master_key_info, regenerate_master_key,
    create_api_key, list_api_keys, get_api_key, update_api_key, delete_api_key,
    setup_2fa, verify_2fa, disable_2fa,
    list_sessions, revoke_session,
    get_audit_logs,
    health_check
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@middleware
async def error_middleware(request, handler):
    """Global error handling middleware"""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error")
        return web.json_response(
            {"error": "internal_error", "message": "An internal error occurred"},
            status=500
        )


@middleware
async def cors_middleware(request, handler):
    """CORS middleware"""
    response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


async def init_app():
    """Initialize the application"""
    app = web.Application(middlewares=[error_middleware, cors_middleware])

    # Store services in app
    app["db"] = db
    app["auth_service"] = auth_service

    # Setup routes
    # Public routes (no auth required)
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/auth/setup/status", check_setup)
    app.router.add_post("/api/auth/setup", setup_owner)
    app.router.add_post("/api/auth/login", login)
    app.router.add_post("/api/auth/login/2fa", login_2fa)
    app.router.add_post("/api/auth/refresh", refresh_token)

    # Protected routes (require authentication)
    app.router.add_post("/api/auth/logout", logout)
    app.router.add_post("/api/auth/logout/all", logout_all)
    app.router.add_get("/api/auth/me", get_me)
    app.router.add_post("/api/auth/password", change_password)

    # Master API Key
    app.router.add_get("/api/auth/master-key", get_master_key_info)
    app.router.add_post("/api/auth/master-key/regenerate", regenerate_master_key)

    # API Keys
    app.router.add_post("/api/auth/keys", create_api_key)
    app.router.add_get("/api/auth/keys", list_api_keys)
    app.router.add_get("/api/auth/keys/{key_id}", get_api_key)
    app.router.add_put("/api/auth/keys/{key_id}", update_api_key)
    app.router.add_delete("/api/auth/keys/{key_id}", delete_api_key)

    # 2FA
    app.router.add_post("/api/auth/2fa/setup", setup_2fa)
    app.router.add_post("/api/auth/2fa/verify", verify_2fa)
    app.router.add_post("/api/auth/2fa/disable", disable_2fa)

    # Sessions
    app.router.add_get("/api/auth/sessions", list_sessions)
    app.router.add_delete("/api/auth/sessions/{session_id}", revoke_session)

    # Audit Logs
    app.router.add_get("/api/auth/audit-logs", get_audit_logs)

    # Startup/Shutdown
    async def on_startup(app):
        logger.info("Starting auth service...")
        await db.connect()
        await auth_service.initialize()
        logger.info("Auth service started")

    async def on_shutdown(app):
        logger.info("Shutting down auth service...")
        await auth_service.close()
        await db.disconnect()
        logger.info("Auth service stopped")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


def main():
    """Main entry point"""
    app = asyncio.run(init_app())
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()