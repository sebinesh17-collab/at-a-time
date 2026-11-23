"""
API Gateway routes
"""
from aiohttp import web
from aiohttp.web import Request, json_response

from ..services.proxy import proxy_service
from ..utils.rate_limiter import rate_limiter


async def health_check(request: Request):
    """Health check endpoint"""
    return json_response({
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    })


async def proxy_handler(request: Request):
    """Handle proxied requests with rate limiting"""
    # Check rate limit
    allowed, headers = await rate_limiter.check_rate_limit(request)
    if not allowed:
        return json_response(
            {"error": "rate_limit_exceeded", "message": "Too many requests"},
            status=429,
            headers=headers
        )

    # Proxy the request
    response = await proxy_service.proxy_request(request)

    # Add rate limit headers to response
    for k, v in headers.items():
        response.headers[k] = v

    return response


async def services_status(request: Request):
    """Get status of all backend services"""
    # This would check health of each service
    # For now return the configured services
    from ..config import SERVICE_ROUTES

    status = {}
    for route, url in SERVICE_ROUTES.items():
        service_name = route.strip("/").replace("/", "-")
        status[service_name] = {
            "url": url,
            "route": route
        }

    return json_response({"services": status})


def setup_routes(app: web.Application):
    """Setup gateway routes"""
    # Health check (no auth required)
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/gateway/services", services_status)

    # Catch-all proxy route - must be last
    app.router.add_route("*", "/{tail:.*}", proxy_handler)