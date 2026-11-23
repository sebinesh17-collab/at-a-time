"""
API Gateway - Proxy service for routing requests to backend services
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from aiohttp import web, ClientSession, ClientTimeout
from aiohttp.web import Request, Response, json_response
import httpx

from ..config import settings, SERVICE_ROUTES

logger = logging.getLogger(__name__)


class ProxyService:
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.session: Optional[ClientSession] = None

    async def initialize(self):
        """Initialize HTTP clients"""
        timeout = ClientTimeout(total=settings.proxy_timeout)
        self.session = ClientSession(timeout=timeout)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.proxy_timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        logger.info("Proxy service initialized")

    async def shutdown(self):
        """Shutdown HTTP clients"""
        if self.session:
            await self.session.close()
        if self.http_client:
            await self.http_client.aclose()
        logger.info("Proxy service shut down")

    def _get_service_url(self, path: str) -> Optional[str]:
        """Get target service URL for a given path"""
        for route_prefix, service_url in SERVICE_ROUTES.items():
            if path.startswith(route_prefix):
                # Replace the route prefix with the service URL
                return path.replace(route_prefix, service_url, 1)
        return None

    def _get_service_name(self, path: str) -> Optional[str]:
        """Get service name for logging"""
        for route_prefix, service_url in SERVICE_ROUTES.items():
            if path.startswith(route_prefix):
                return route_prefix.strip("/").replace("/", "-")
        return None

    async def proxy_request(self, request: Request) -> Response:
        """Proxy request to backend service"""
        target_url = self._get_service_url(request.path)
        service_name = self._get_service_name(request.path)

        if not target_url:
            return json_response(
                {"error": "not_found", "message": f"No service found for path: {request.path}"},
                status=404
            )

        # Prepare headers to forward
        headers = dict(request.headers)
        # Remove hop-by-hop headers
        for h in ["host", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
                  "te", "trailers", "transfer-encoding", "upgrade"]:
            headers.pop(h, None)

        # Add owner_id from auth middleware
        if "owner_id" in request:
            headers["X-Owner-ID"] = request["owner_id"]
        if "is_master_key" in request:
            headers["X-Is-Master-Key"] = str(request["is_master_key"]).lower()
        if "session_id" in request:
            headers["X-Session-ID"] = request["session_id"]

        # Get query string
        query_string = request.query_string
        if query_string:
            target_url = f"{target_url}?{query_string}"

        # Get request body
        body = None
        if request.can_read_body:
            body = await request.read()

        try:
            # Forward request using httpx
            response = await self.http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query if query_string else None,
            )

            # Prepare response headers
            response_headers = {}
            for h in ["content-type", "cache-control", "etag", "last-modified"]:
                if h in response.headers:
                    response_headers[h] = response.headers[h]

            return web.Response(
                body=response.content,
                status=response.status_code,
                headers=response_headers
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout proxying to {service_name}: {target_url}")
            return json_response(
                {"error": "gateway_timeout", "message": "Backend service timeout"},
                status=504
            )
        except httpx.ConnectError:
            logger.error(f"Connection error to {service_name}: {target_url}")
            return json_response(
                {"error": "bad_gateway", "message": "Backend service unavailable"},
                status=502
            )
        except Exception as e:
            logger.exception(f"Error proxying to {service_name}: {e}")
            return json_response(
                {"error": "internal_error", "message": "Proxy error"},
                status=500
            )


proxy_service = ProxyService()