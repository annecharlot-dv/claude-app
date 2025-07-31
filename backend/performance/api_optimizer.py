"""
API Performance Optimizer
Implements response caching, compression, and optimization middleware
"""

import gzip
import json
import logging
import time
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .cache_manager import get_cache_manager
from .monitor import get_performance_monitor

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for API performance optimization"""

    def __init__(
        self, app, enable_caching: bool = True, enable_compression: bool = True
    ):
        super().__init__(app)
        self.enable_caching = enable_caching
        self.enable_compression = enable_compression
        self.cache_manager = None
        self.performance_monitor = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Initialize managers if not done
        if self.cache_manager is None:
            self.cache_manager = await get_cache_manager()
        if self.performance_monitor is None:
            self.performance_monitor = await get_performance_monitor()

        # Extract tenant info for caching
        tenant_id = self._extract_tenant_id(request)

        # Check cache for GET requests
        if request.method == "GET" and self.enable_caching:
            cached_response = await self._get_cached_response(request, tenant_id)
            if cached_response:
                # Record cache hit
                execution_time = (time.time() - start_time) * 1000
                await self.performance_monitor.record_metric(
                    "api_cache_hit",
                    execution_time,
                    {"path": request.url.path},
                    tenant_id,
                )
                return cached_response

        # Process request
        try:
            response = await call_next(request)
            execution_time = (time.time() - start_time) * 1000

            # Record performance metrics
            await self.performance_monitor.record_metric(
                "response_time",
                execution_time,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                },
                tenant_id,
            )

            # Cache successful GET responses
            if (
                request.method == "GET"
                and response.status_code == 200
                and self.enable_caching
                and self._is_cacheable_path(request.url.path)
            ):

                await self._cache_response(request, response, tenant_id)

            # Apply compression if enabled
            if self.enable_compression and self._should_compress(request, response):
                response = await self._compress_response(response)

            # Add performance headers
            response.headers["X-Response-Time"] = f"{execution_time:.2f}ms"
            response.headers["X-Cache"] = "MISS"

            return response

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            await self.performance_monitor.record_metric(
                "api_error",
                execution_time,
                {
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                tenant_id,
            )
            raise

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        # Try to get from subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api"]:
                return subdomain

        # Try to get from headers
        return request.headers.get("X-Tenant-ID")

    async def _get_cached_response(
        self, request: Request, tenant_id: str
    ) -> Optional[Response]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(request, tenant_id)
        cached_data = await self.cache_manager.get(cache_key)

        if cached_data:
            response = JSONResponse(
                content=cached_data["content"],
                status_code=cached_data["status_code"],
                headers=cached_data.get("headers", {}),
            )
            response.headers["X-Cache"] = "HIT"
            return response

        return None

    async def _cache_response(
        self, request: Request, response: Response, tenant_id: str
    ):
        """Cache response data"""
        try:
            # Only cache JSON responses
            if response.headers.get("content-type", "").startswith("application/json"):
                cache_key = self._generate_cache_key(request, tenant_id)

                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Parse JSON content
                content = json.loads(body.decode())

                # Determine cache TTL based on path
                ttl = self._get_cache_ttl(request.url.path)

                # Cache the response
                cache_data = {
                    "content": content,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }

                await self.cache_manager.set(
                    cache_key,
                    cache_data,
                    ttl=ttl,
                    tags=[f"tenant:{tenant_id}", "api_response"],
                )

                # Recreate response with cached body
                response = JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers=response.headers,
                )

        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

    def _generate_cache_key(self, request: Request, tenant_id: str) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.method,
            request.url.path,
            str(request.query_params),
            tenant_id or "no_tenant",
        ]
        return ":".join(key_parts)

    def _is_cacheable_path(self, path: str) -> bool:
        """Check if path should be cached"""
        cacheable_patterns = [
            "/api/cms/pages",
            "/api/forms",
            "/api/cms/templates",
            "/api/leads",
            "/api/tours/slots",
        ]

        non_cacheable_patterns = ["/api/auth/", "/api/performance/", "/api/health"]

        # Check non-cacheable first
        for pattern in non_cacheable_patterns:
            if pattern in path:
                return False

        # Check cacheable patterns
        for pattern in cacheable_patterns:
            if pattern in path:
                return True

        return False

    def _get_cache_ttl(self, path: str) -> int:
        """Get cache TTL based on path"""
        ttl_map = {
            "/api/cms/pages": 1800,  # 30 minutes
            "/api/cms/templates": 3600,  # 1 hour
            "/api/forms": 1800,  # 30 minutes
            "/api/leads": 300,  # 5 minutes
            "/api/tours/slots": 600,  # 10 minutes
        }

        for pattern, ttl in ttl_map.items():
            if pattern in path:
                return ttl

        return 600  # Default 10 minutes

    def _should_compress(self, request: Request, response: Response) -> bool:
        """Check if response should be compressed"""
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "")
        compressible_types = [
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
        ]

        return any(ct in content_type for ct in compressible_types)

    async def _compress_response(self, response: Response) -> Response:
        """Compress response using gzip"""
        try:
            # Get response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Compress body
            compressed_body = gzip.compress(body)

            # Create new response with compressed body
            compressed_response = Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type,
            )

            # Add compression headers
            compressed_response.headers["Content-Encoding"] = "gzip"
            compressed_response.headers["Content-Length"] = str(len(compressed_body))

            return compressed_response

        except Exception as e:
            logger.warning(f"Failed to compress response: {e}")
            return response


class ResponseOptimizer:
    """Optimizes API responses for better performance"""

    @staticmethod
    def paginate_response(data: list, page: int = 1, limit: int = 25) -> Dict[str, Any]:
        """Paginate large response data"""
        total = len(data)
        start = (page - 1) * limit
        end = start + limit

        return {
            "data": data[start:end],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
                "has_next": end < total,
                "has_prev": page > 1,
            },
        }

    @staticmethod
    def optimize_fields(
        data: Dict[str, Any], fields: Optional[list] = None
    ) -> Dict[str, Any]:
        """Return only requested fields to reduce response size"""
        if not fields:
            return data

        if isinstance(data, dict):
            return {key: value for key, value in data.items() if key in fields}
        elif isinstance(data, list):
            return [
                {key: item.get(key) for key in fields if key in item} for item in data
            ]

        return data

    @staticmethod
    def add_etag(response: Response, data: Any) -> Response:
        """Add ETag header for caching"""
        import hashlib

        # Generate ETag from data
        data_str = json.dumps(data, sort_keys=True, default=str)
        etag = hashlib.md5(data_str.encode()).hexdigest()

        response.headers["ETag"] = f'"{etag}"'
        response.headers["Cache-Control"] = "max-age=300"  # 5 minutes

        return response


# Decorator for caching API responses
def cache_response(ttl: int = 600, tags: list = None):
    """Decorator to cache API response"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and tenant info
            request = None
            tenant_id = None

            for arg in args:
                if hasattr(arg, "method"):  # Request object
                    request = arg
                elif hasattr(arg, "tenant_id"):  # User object
                    tenant_id = arg.tenant_id

            if not request:
                # No request found, execute normally
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = (
                f"{func.__name__}:{request.url.path}:" f"{str(request.query_params)}"
            )
            if tenant_id:
                cache_key += f":{tenant_id}"

            # Try to get from cache
            cache_manager = await get_cache_manager()
            cached_result = await cache_manager.get(cache_key)

            if cached_result:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Cache the result
            cache_tags = tags or []
            if tenant_id:
                cache_tags.append(f"tenant:{tenant_id}")

            await cache_manager.set(cache_key, result, ttl=ttl, tags=cache_tags)

            return result

        return wrapper

    return decorator
