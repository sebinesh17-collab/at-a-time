"""
API Gateway Main Entry Point
"""
from aiohttp import web
from aiohttp.web import middleware
import asyncio
import logging

from .config import settings
from .middleware.auth import auth_middleware_instance
from .services.proxy import proxy_service
from .utils.rate_limiter import rate_limiter
from .routes.gateway import setup_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error in API Gateway")
        return web.json_response(
            {"error": "internal_error", "message": "An internal error occurred"},
            status=500
        )


@middleware
async def cors_middleware(request, handler):
    # Handle preflight
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


async def init_app():
    app = web.Application(middlewares=[
        error_middleware,
        cors_middleware,
        auth_middleware_instance.auth_middleware
    ])

    app["proxy"] = proxy_service
    app["rate_limiter"] = rate_limiter

    setup_routes(app)

    async def on_startup(app):
        logger.info("Starting API Gateway...")
        await auth_middleware_instance.initialize()
        await proxy_service.initialize()
        await rate_limiter.initialize()
        logger.info("API Gateway started on port %d", settings.port)

    async def on_shutdown(app):
        logger.info("Shutting down API Gateway...")
        await auth_middleware_instance.close()
        await proxy_service.shutdown()
        await rate_limiter.close()
        logger.info("API Gateway stopped")

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


def main():
    app = asyncio.run(init_app())
    web.run_app(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()