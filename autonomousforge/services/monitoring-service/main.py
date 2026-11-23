"""
Monitoring Service Main Entry Point
"""
from aiohttp import web
from aiohttp.web import middleware
import asyncio
import logging

from .config import settings
from .database import db
from .services.monitor import monitor
from .routes.monitor import setup_routes

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
    app["monitor"] = monitor

    setup_routes(app)

    async def on_startup(app):
        logger.info("Starting monitoring service...")
        await db.connect()
        await monitor.initialize()
        logger.info("Monitoring service started")

    async def on_shutdown(app):
        logger.info("Shutting down monitoring service...")
        await monitor.shutdown()
        await db.disconnect()
        logger.info("Monitoring service stopped")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


def main():
    app = asyncio.run(init_app())
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()