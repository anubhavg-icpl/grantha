"""Logging middleware for request/response tracking and debugging."""

import time
import json
import logging
import structlog
from typing import Any, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 1024,  # Max bytes to log
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        
    async def get_request_body(self, request: Request) -> str:
        """Safely get request body for logging."""
        try:
            body = await request.body()
            if len(body) > self.max_body_size:
                return f"<truncated body: {len(body)} bytes>"
            return body.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"<error reading body: {str(e)}>"
    
    def get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information."""
        return {
            "client_ip": self.get_client_ip(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "referer": request.headers.get("Referer", ""),
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with comprehensive logging."""
        start_time = time.time()
        
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate request ID for tracking
        request_id = f"{int(time.time())}-{hash(str(request.url)) % 10000}"
        
        # Log request
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": {
                k: v for k, v in request.headers.items() 
                if k.lower() not in ["authorization", "cookie"]  # Exclude sensitive headers
            },
            **self.get_client_info(request)
        }
        
        # Add request body if enabled
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            # Save body for later since it can only be read once
            body = await request.body()
            request._body = body  # Cache for the actual handler
            
            if len(body) <= self.max_body_size:
                try:
                    request_log["body"] = body.decode('utf-8', errors='ignore')
                except Exception:
                    request_log["body"] = f"<binary data: {len(body)} bytes>"
            else:
                request_log["body"] = f"<large body: {len(body)} bytes>"
        
        logger.info("Request received", **request_log)
        
        # Process request
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            response_log = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": len(response.body) if hasattr(response, 'body') else 0
            }
            
            # Add response body if enabled and successful
            if (self.log_response_body and 
                response.status_code < 400 and 
                hasattr(response, 'body')):
                body_size = len(response.body)
                if body_size <= self.max_body_size:
                    try:
                        response_log["body"] = response.body.decode('utf-8', errors='ignore')
                    except Exception:
                        response_log["body"] = f"<binary response: {body_size} bytes>"
                else:
                    response_log["body"] = f"<large response: {body_size} bytes>"
            
            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            if response.status_code >= 400:
                logger.warning("Request completed with error", **response_log)
            else:
                logger.info("Request completed successfully", **response_log)
                
            # Log performance warnings
            if duration > 2.0:  # Slow request threshold
                logger.warning(
                    "Slow request detected",
                    request_id=request_id,
                    duration_ms=response_log["duration_ms"],
                    path=request.url.path,
                    method=request.method
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                exception=str(e),
                exception_type=type(e).__name__,
                duration_ms=round(duration * 1000, 2),
                path=request.url.path,
                method=request.method
            )
            raise