"""
File Service Main Entry Point
"""
from aiohttp import web
from aiohttp.web import middleware
import asyncio
import logging

from .config import settings
from .database import db
from .services.files import file_service
from .routes.files import setup_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@middleware
async def error_middleware(request, handler):
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
    response = await handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


async def init_app():
    app = web.Application(middlewares=[error_middleware, cors_middleware])

    app["db"] = db
    app["file_service"] = file_service

    setup_routes(app)

    async def on_startup(app):
        logger.info("Starting file service...")
        await db.connect()
        await file_service.initialize()
        logger.info("File service started")

    async def on_shutdown(app):
        logger.info("Shutting down file service...")
        await db.disconnect()
        logger.info("File service stopped")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


def main():
    app = asyncio.run(init_app())
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()