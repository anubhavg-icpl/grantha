"""Caching middleware for response optimization."""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple
from cachetools import TTLCache
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses."""
    
    def __init__(
        self,
        app: ASGIApp,
        max_size: int = 1000,  # Max cached items
        default_ttl: int = 300,  # Default TTL in seconds (5 minutes)
        cache_config: Dict[str, Tuple[int, List[str]]] = None
    ):
        super().__init__(app)
        self.cache = TTLCache(maxsize=max_size, ttl=default_ttl)
        self.default_ttl = default_ttl
        
        # Configure cache settings per endpoint
        # Format: {path_prefix: (ttl_seconds, cacheable_methods)}
        self.cache_config = cache_config or {}
        
        # Default cache configuration
        self.endpoint_cache_config = {
            '/models': (600, ['GET']),        # Cache models for 10 minutes
            '/wiki/search': (300, ['GET']),   # Cache search results for 5 minutes
            '/health': (60, ['GET']),         # Cache health check for 1 minute
            '/': (3600, ['GET']),             # Cache root endpoint for 1 hour
            **self.cache_config
        }
        
        # Endpoints that should never be cached
        self.no_cache_patterns = [
            '/chat',      # Chat responses should be unique
            '/auth',      # Authentication requests
            '/admin',     # Admin operations
        ]
    
    def should_cache(self, request: Request) -> Tuple[bool, int]:
        """Determine if request should be cached and return TTL."""
        path = request.url.path
        method = request.method
        
        # Check if path should never be cached
        for pattern in self.no_cache_patterns:
            if path.startswith(pattern):
                return False, 0
        
        # Check specific cache configuration
        for endpoint_pattern, (ttl, methods) in self.endpoint_cache_config.items():
            if path.startswith(endpoint_pattern) and method in methods:
                return True, ttl
        
        # Default: don't cache unless explicitly configured
        return False, 0
    
    def generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        # Include method, path, query params, and relevant headers
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items())),
        ]
        
        # Include certain headers that might affect response
        cache_headers = ['accept', 'accept-language', 'authorization']
        for header in cache_headers:
            value = request.headers.get(header)
            if value:
                key_components.append(f"{header}:{value}")
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_cacheable_response(self, response: Response) -> bool:
        """Check if response is cacheable."""
        # Only cache successful responses
        if response.status_code != 200:
            return False
        
        # Don't cache responses with certain headers
        no_cache_headers = ['set-cookie', 'authorization']
        for header in no_cache_headers:
            if header in response.headers:
                return False
        
        return True
    
    async def get_cached_response(self, cache_key: str) -> Optional[Response]:
        """Get response from cache."""
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                status_code, headers, body = cached_data
                response = JSONResponse(
                    content=json.loads(body),
                    status_code=status_code,
                    headers=dict(headers)
                )
                # Add cache hit header
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key[:16] + "..."
                return response
        except Exception as e:
            logger.warning(f"Error retrieving cached response: {e}")
            
        return None
    
    async def cache_response(
        self, 
        cache_key: str, 
        response: Response, 
        ttl: int
    ) -> None:
        """Cache the response."""
        try:
            # Read response body
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            
            # Store in cache
            self.cache[cache_key] = (
                response.status_code,
                list(response.headers.items()),
                body_bytes.decode('utf-8')
            )
            
            # Create new response with the same content
            new_response = Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
            
            # Add cache headers
            new_response.headers["X-Cache"] = "MISS"
            new_response.headers["X-Cache-Key"] = cache_key[:16] + "..."
            new_response.headers["Cache-Control"] = f"max-age={ttl}"
            
            return new_response
            
        except Exception as e:
            logger.warning(f"Error caching response: {e}")
            # Return original response if caching fails
            response.headers["X-Cache"] = "ERROR"
            return response
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with caching logic."""
        should_cache, ttl = self.should_cache(request)
        
        if not should_cache:
            # Don't cache, process normally
            response = await call_next(request)
            response.headers["X-Cache"] = "SKIP"
            return response
        
        # Generate cache key
        cache_key = self.generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await self.get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for key: {cache_key[:16]}...")
            return cached_response
        
        # Process request
        response = await call_next(request)
        
        # Cache response if appropriate
        if self.is_cacheable_response(response):
            logger.debug(f"Caching response for key: {cache_key[:16]}...")
            cached_response = await self.cache_response(cache_key, response, ttl)
            if cached_response:
                return cached_response
        
        # Add cache miss header
        response.headers["X-Cache"] = "MISS"
        return response
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hit_info": getattr(self.cache, 'hit_info', {}),
        }
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache, optionally by pattern."""
        if pattern is None:
            cleared = len(self.cache)
            self.cache.clear()
            logger.info(f"Cleared entire cache: {cleared} items")
            return cleared
        
        # Clear by pattern (basic implementation)
        keys_to_remove = []
        for key in list(self.cache.keys()):
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        logger.info(f"Cleared cache by pattern '{pattern}': {len(keys_to_remove)} items")
        return len(keys_to_remove)