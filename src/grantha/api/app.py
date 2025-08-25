"""FastAPI application factory for the Grantha platform."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import get_config
from ..core.logging_config import setup_logging
from .routes import auth_router, models_router, wiki_router, chat_router, research_router, simple_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Setup logging
    setup_logging()
    
    # Get configuration
    config = get_config()
    
    # Initialize FastAPI app
    app = FastAPI(
        title="ग्रंथ (Grantha) API",
        description="Knowledge management and documentation API powered by AI",
        version="1.0.0"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    # Include routers
    app.include_router(auth_router, prefix="/auth", tags=["authentication"])
    app.include_router(models_router, prefix="/models", tags=["models"])
    app.include_router(wiki_router, prefix="/wiki", tags=["wiki"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])
    app.include_router(research_router, prefix="/research", tags=["research"])
    app.include_router(simple_router, prefix="/simple", tags=["simple"])

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "ग्रंथ (Grantha) API",
            "version": "1.0.0",
            "description": "AI-powered knowledge management and documentation platform"
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    logger.info("Grantha API application created successfully")
    return app