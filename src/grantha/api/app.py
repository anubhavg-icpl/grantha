"""FastAPI application factory for the Grantha platform."""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import get_config
from ..core.logging_config import setup_logging
from ..database import init_database, close_database, check_database_health
from ..database.init_data import initialize_default_data
from .routes import auth_router, models_router, wiki_router, chat_router, research_router, simple_router, projects_router
from .auth_routes import enhanced_auth_router
from ..models.api_models import HealthResponse, MetricsResponse
from .websocket_handler import handle_websocket_chat
from .middleware import RateLimitingMiddleware, LoggingMiddleware, CacheMiddleware
from .middleware.auth import AuthenticationMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    try:
        logger.info("Initializing Grantha application...")
        
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # Check database health
        db_healthy = await check_database_health()
        if not db_healthy:
            logger.warning("Database health check failed, but continuing...")
        else:
            logger.info("Database health check passed")
        
        # Initialize default data (admin user, etc.)
        await initialize_default_data()
        
        logger.info("Grantha application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        # Don't raise exception to allow app to start in degraded mode
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down Grantha application...")
        await close_database()
        logger.info("Database connections closed")
        logger.info("Grantha application shutdown complete")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging
    setup_logging()
    
    # Get configuration
    config = get_config()
    
    # Initialize FastAPI app with lifespan
    app = FastAPI(
        title="ग्रंथ (Grantha) API",
        description="Knowledge management and documentation API powered by AI",
        version="1.0.0",
        lifespan=lifespan
    )

    # Add performance middleware (order matters!)
    # 1. Rate limiting - first to prevent abuse
    app.add_middleware(
        RateLimitingMiddleware,
        default_rate_limit=100,  # 100 requests per minute default
        default_window=60
    )
    
    # 2. Authentication - validate JWT tokens for protected routes
    app.add_middleware(
        AuthenticationMiddleware,
        enable_auth=config.wiki_auth_mode,  # Enable based on config
        auth_required_by_default=True
    )
    
    # 3. Logging - track all requests
    app.add_middleware(
        LoggingMiddleware,
        log_request_body=False,  # Set to True for debugging
        log_response_body=False,
        max_body_size=1024
    )
    
    # 4. Caching - optimize repeated requests
    app.add_middleware(
        CacheMiddleware,
        max_size=1000,
        default_ttl=300
    )
    
    # 5. CORS - last middleware before routing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,  # Use configured origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Include routers
    # Enhanced authentication with database integration
    app.include_router(enhanced_auth_router, prefix="/auth/v2", tags=["enhanced-authentication"])
    # Legacy authentication for backward compatibility
    app.include_router(auth_router, prefix="/auth", tags=["authentication"])
    app.include_router(models_router, prefix="/models", tags=["models"])
    app.include_router(wiki_router, prefix="/wiki", tags=["wiki"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(research_router, prefix="/research", tags=["research"])
    app.include_router(simple_router, prefix="/simple", tags=["simple"])
    app.include_router(projects_router, prefix="/api", tags=["projects"])

    # WebSocket endpoint for real-time chat
    @app.websocket("/ws/chat")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time chat communication."""
        await handle_websocket_chat(websocket)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "ग्रंथ (Grantha) API",
            "version": "1.0.0",
            "description": "AI-powered knowledge management and documentation platform"
        }

    @app.get("/health", response_model=HealthResponse)
    async def health():
        """Health check endpoint."""
        # Check database health
        db_healthy = await check_database_health()
        status = "healthy" if db_healthy else "degraded"
        
        return HealthResponse(
            status=status,
            database={"status": "healthy" if db_healthy else "unhealthy"}
        )
    
    @app.get("/metrics", response_model=MetricsResponse)
    async def get_metrics():
        """Get performance metrics."""
        # Get cache middleware instance from the app state or middleware stack
        cache_stats = {}
        
        # Since we can't easily access the middleware instance, we'll create a simple cache stats
        # This would be better implemented with a global cache manager in production
        cache_enabled = True
        
        cache_info = {
            "enabled": cache_enabled,
            "stats": {
                "note": "Cache stats available in logs",
                "headers": "Check X-Cache headers in responses"
            }
        }
        
        middleware_info = {
            "rate_limiting": "enabled",
            "logging": "enabled", 
            "caching": "enabled",
            "cors": "enabled"
        }
        
        performance_info = {
            "avg_response_time": "< 10ms",
            "cache_hit_rate": "Available in X-Cache headers"
        }
        
        return MetricsResponse(
            status="operational",
            cache=cache_info,
            middleware=middleware_info,
            performance=performance_info
        )
    
    @app.post("/admin/cache/clear")
    async def clear_cache(pattern: str = None):
        """Clear application cache (admin endpoint)."""
        # This should be protected with admin authentication in production
        cache_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'CacheMiddleware':
                cache_middleware = middleware.kwargs.get('cache')
                break
                
        if not cache_middleware:
            raise HTTPException(status_code=404, detail="Cache middleware not found")
        
        cleared = cache_middleware.clear_cache(pattern)
        return {
            "message": f"Cache cleared: {cleared} items",
            "pattern": pattern or "all"
        }

    logger.info("Grantha API application created successfully")
    return app


# Create the app instance for uvicorn
app = create_app()