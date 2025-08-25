"""API routes for the Grantha platform."""

import logging
import os
from fastapi import APIRouter, HTTPException, Query, Request, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any, Literal
import google.generativeai as genai

from ..models.api_models import (
    AuthorizationConfig,
    ModelConfig,
    WikiGenerationRequest,
    DeepResearchRequest,
    ChatRequest,
    ChatResponse,
    SimpleRequest,
    RAGRequest,
    WikiCacheRequest,
    WikiExportRequest
)
from ..core.config import get_config, configs

logger = logging.getLogger(__name__)

# Initialize Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
else:
    gemini_model = None
    logger.warning("Google API key not found. Chat functionality will be limited.")

# Create routers
auth_router = APIRouter()
models_router = APIRouter()
wiki_router = APIRouter()
chat_router = APIRouter()
research_router = APIRouter()
simple_router = APIRouter()


# Authentication routes
@auth_router.get("/status")
async def get_auth_status():
    """Check if authentication is required for the wiki."""
    config = get_config()
    return {"auth_required": config.wiki_auth_mode}


@auth_router.post("/validate")
async def validate_auth_code(request: AuthorizationConfig):
    """Check authorization code."""
    config = get_config()
    return {"success": config.wiki_auth_code == request.code}


# Language configuration route
@auth_router.get("/lang/config")
async def get_lang_config():
    """Get language configuration."""
    return configs.get("lang", {})


# Models routes
@models_router.get("/config", response_model=ModelConfig)
async def get_model_config():
    """
    Get available model providers and their models.
    
    This endpoint returns the configuration of available model providers and their
    respective models that can be used throughout the application.
    """
    try:
        generator_config = configs.get("generator", {})
        
        if not generator_config or "providers" not in generator_config:
            # Return default configuration
            return ModelConfig(
                providers=[],
                defaultProvider="google"
            )
        
        providers = []
        for provider_id, provider_config in generator_config["providers"].items():
            if provider_config.get("enabled", True):
                provider = {
                    "id": provider_id,
                    "name": provider_config.get("name", provider_id.title()),
                    "models": [
                        {"id": model_id, "name": model_config.get("name", model_id)}
                        for model_id, model_config in provider_config.get("models", {}).items()
                    ],
                    "supportsCustomModel": provider_config.get("supportsCustomModel", False)
                }
                providers.append(provider)
        
        default_provider = generator_config.get("default_provider", "google")
        
        return ModelConfig(
            providers=providers,
            defaultProvider=default_provider
        )
        
    except Exception as e:
        logger.error(f"Error getting model config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model configuration")


# Wiki routes (placeholder - will need to import actual implementations)
@wiki_router.post("/generate")
async def generate_wiki(request: WikiGenerationRequest):
    """Generate wiki documentation for a repository."""
    # This will need to be implemented with the actual wiki generator
    raise HTTPException(status_code=501, detail="Not implemented yet")


@wiki_router.post("/cache")
async def save_wiki_cache(request: WikiCacheRequest):
    """Save wiki cache data."""
    # This will need to be implemented with the actual cache logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


@wiki_router.post("/export")
async def export_wiki(request: WikiExportRequest):
    """Export wiki pages in the specified format."""
    # This will need to be implemented with the actual export logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Chat routes (placeholder)
@chat_router.post("/completion")
async def chat_completion(request: ChatRequest):
    """Handle chat completion requests."""
    # This will need to be implemented with the actual chat logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Research routes (placeholder)
@research_router.post("/deep")
async def deep_research(request: DeepResearchRequest):
    """Perform deep research on a topic."""
    # This will need to be implemented with the actual research logic
    raise HTTPException(status_code=501, detail="Not implemented yet")


# Simple routes
@simple_router.post("/chat")
async def simple_chat(request: SimpleRequest):
    """Handle simple chat requests."""
    try:
        # Use actual Gemini model if available
        if gemini_model:
            try:
                response = gemini_model.generate_content(request.user_query)
                return {
                    "message": response.text,
                    "provider": request.provider or "google",
                    "model": request.model or "gemini-2.0-flash-exp",
                    "status": "success"
                }
            except Exception as gemini_error:
                logger.error(f"Gemini API error: {str(gemini_error)}")
                # Fallback to echo mode if Gemini fails
                return {
                    "message": f"Echo (Gemini error): {request.user_query}",
                    "provider": "fallback",
                    "model": "echo",
                    "status": "fallback",
                    "error": str(gemini_error)
                }
        else:
            # Fallback to echo mode if no API key
            return {
                "message": f"Echo (No API key): {request.user_query}",
                "provider": "fallback", 
                "model": "echo",
                "status": "no_api_key"
            }
    except Exception as e:
        logger.error(f"Error in simple chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@simple_router.post("/rag")
async def simple_rag(request: RAGRequest):
    """Handle RAG (Retrieval-Augmented Generation) requests."""
    try:
        # For now, return a mock response to test the API integration
        return {
            "answer": f"RAG Response for query: '{request.query}' from repo: {request.repo_url}",
            "sources": ["mock_source_1.py", "mock_source_2.md"],
            "provider": request.provider or "mock",
            "model": request.model or "mock-model",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error in simple RAG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))