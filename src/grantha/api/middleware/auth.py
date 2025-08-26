"""Authentication middleware for JWT token validation."""

import logging
from typing import Optional, Callable, Awaitable, Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException, status

from ...utils.jwt_service import jwt_service

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """JWT Authentication middleware for protected routes."""
    
    # Routes that don't require authentication
    PUBLIC_ROUTES: Set[str] = {
        "/",
        "/health",
        "/metrics", 
        "/auth/status",
        "/auth/validate",
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/auth/lang/config",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    # Route prefixes that don't require authentication
    PUBLIC_PREFIXES: Set[str] = {
        "/static/",
        "/docs",
        "/redoc"
    }
    
    def __init__(
        self, 
        app,
        enable_auth: bool = True,
        auth_required_by_default: bool = True
    ):
        super().__init__(app)
        self.enable_auth = enable_auth
        self.auth_required_by_default = auth_required_by_default
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]) -> JSONResponse:
        """Process request and validate authentication if required."""
        
        # Skip authentication if disabled
        if not self.enable_auth:
            return await call_next(request)
        
        # Check if route requires authentication
        if not self._requires_auth(request):
            return await call_next(request)
        
        # Extract and validate token
        auth_result = await self._authenticate_request(request)
        
        if not auth_result["authenticated"]:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "authentication_required",
                    "message": auth_result["error"],
                    "code": status.HTTP_401_UNAUTHORIZED
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user info to request state
        request.state.user_id = auth_result["user_id"]
        request.state.token_info = auth_result["token_info"]
        
        response = await call_next(request)
        
        # Add auth headers to response
        if auth_result["token_info"]:
            response.headers["X-User-ID"] = auth_result["user_id"]
            response.headers["X-Token-Valid"] = "true"
        
        return response
    
    def _requires_auth(self, request: Request) -> bool:
        """Check if the current route requires authentication."""
        path = request.url.path.lower()
        
        # Check exact matches
        if path in self.PUBLIC_ROUTES:
            return False
        
        # Check prefixes
        for prefix in self.PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return False
        
        # Check if it's an OPTIONS request (for CORS preflight)
        if request.method == "OPTIONS":
            return False
        
        return self.auth_required_by_default
    
    async def _authenticate_request(self, request: Request) -> dict:
        """Authenticate the request and return result."""
        
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return {
                "authenticated": False,
                "error": "Missing authorization header",
                "user_id": None,
                "token_info": None
            }
        
        # Parse Bearer token
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                return {
                    "authenticated": False,
                    "error": "Invalid authorization scheme. Use Bearer token",
                    "user_id": None,
                    "token_info": None
                }
        except ValueError:
            return {
                "authenticated": False,
                "error": "Invalid authorization header format",
                "user_id": None,
                "token_info": None
            }
        
        # Validate access token
        token_payload = jwt_service.validate_access_token(token)
        if not token_payload:
            return {
                "authenticated": False,
                "error": "Invalid or expired access token",
                "user_id": None,
                "token_info": None
            }
        
        user_id = token_payload.get("user_id")
        if not user_id:
            return {
                "authenticated": False,
                "error": "Invalid token: missing user ID",
                "user_id": None,
                "token_info": None
            }
        
        return {
            "authenticated": True,
            "error": None,
            "user_id": user_id,
            "token_info": token_payload
        }


def get_current_user(request: Request) -> Optional[str]:
    """Get the current authenticated user ID from request state."""
    return getattr(request.state, 'user_id', None)


def get_token_info(request: Request) -> Optional[dict]:
    """Get the current token information from request state."""
    return getattr(request.state, 'token_info', None)


def require_auth(request: Request) -> str:
    """
    Dependency to require authentication and return user ID.
    Raises HTTPException if not authenticated.
    """
    user_id = get_current_user(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_id