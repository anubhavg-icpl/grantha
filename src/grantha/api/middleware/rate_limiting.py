"""Rate limiting middleware for the Grantha API."""

import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter using sliding window algorithm."""
    
    def __init__(self):
        # Store timestamps for each client: {client_id: deque of timestamps}
        self.clients: Dict[str, Deque[float]] = defaultdict(deque)
        
    def is_allowed(self, client_id: str, limit: int, window: int) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed within rate limits.
        
        Args:
            client_id: Unique identifier for client
            limit: Max requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        timestamps = self.clients[client_id]
        
        # Remove old timestamps outside the window
        while timestamps and timestamps[0] <= now - window:
            timestamps.popleft()
            
        current_count = len(timestamps)
        
        # Rate limit info for headers
        rate_limit_info = {
            'limit': limit,
            'remaining': max(0, limit - current_count),
            'reset': int(now + window) if timestamps else int(now + window),
            'window': window
        }
        
        if current_count >= limit:
            return False, rate_limit_info
            
        # Add current request timestamp
        timestamps.append(now)
        rate_limit_info['remaining'] = max(0, limit - len(timestamps))
        
        return True, rate_limit_info


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with configurable limits per endpoint."""
    
    def __init__(
        self,
        app: ASGIApp,
        default_rate_limit: int = 100,  # requests per minute
        default_window: int = 60,  # 60 seconds
        rate_limit_config: Dict[str, Tuple[int, int]] = None
    ):
        super().__init__(app)
        self.default_rate_limit = default_rate_limit
        self.default_window = default_window
        self.rate_limit_config = rate_limit_config or {}
        self.rate_limiter = InMemoryRateLimiter()
        
        # Special rate limits for different endpoints
        self.endpoint_limits = {
            '/chat': (20, 60),      # 20 requests per minute for chat
            '/wiki': (50, 60),      # 50 requests per minute for wiki
            '/research': (10, 60),  # 10 requests per minute for research
            '/models': (30, 60),    # 30 requests per minute for models
            **self.rate_limit_config
        }
        
    def get_client_id(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get client IP from headers (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
            
        # Include user agent for additional uniqueness
        user_agent = request.headers.get("User-Agent", "")[:50]  # Truncate UA
        return f"{client_ip}:{hash(user_agent) % 10000}"
    
    def get_rate_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit and window for a given path."""
        for endpoint, (limit, window) in self.endpoint_limits.items():
            if path.startswith(endpoint):
                return limit, window
        return self.default_rate_limit, self.default_window
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks and root
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
            
        client_id = self.get_client_id(request)
        path = request.url.path
        limit, window = self.get_rate_limit(path)
        
        # Check rate limit
        is_allowed, rate_info = self.rate_limiter.is_allowed(client_id, limit, window)
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_id} on {path}. "
                f"Limit: {limit}/{window}s"
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window} seconds",
                    "retry_after": window
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info['limit']),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info['reset']),
                    "Retry-After": str(window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(rate_info['reset'])
        response.headers["X-RateLimit-Window"] = str(rate_info['window'])
        
        return response