"""API routes for the Grantha platform."""

import logging
import os
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Request, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any, Literal, AsyncGenerator
import google.generativeai as genai

from ..models.api_models import (
    AuthorizationConfig,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    TokenInfoResponse,
    ModelConfig,
    WikiGenerationRequest,
    DeepResearchRequest,
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    SimpleRequest,
    RAGRequest,
    WikiCacheRequest,
    WikiExportRequest,
    WikiPage,
    AuthStatusResponse,
    AuthValidationResponse,
    LanguageConfigResponse,
    SimpleResponse,
    HealthResponse,
    MetricsResponse,
    WikiGenerationResponse
)
from ..core.config import get_config, configs
from ..utils.jwt_service import jwt_service

logger = logging.getLogger(__name__)

# Wiki cache directory setup
def get_grantha_cache_root() -> str:
    """Get the Grantha cache root directory."""
    return os.path.expanduser(os.path.join("~", ".grantha"))

WIKI_CACHE_DIR = os.path.join(get_grantha_cache_root(), "wikicache")

# Ensure cache directory exists
os.makedirs(WIKI_CACHE_DIR, exist_ok=True)

def get_wiki_cache_path(owner: str, repo: str, repo_type: str, language: str) -> str:
    """Generate the file path for a given wiki cache."""
    filename = f"grantha_cache_{repo_type}_{owner}_{repo}_{language}.json"
    return os.path.join(WIKI_CACHE_DIR, filename)

def generate_markdown_export(pages: List[WikiPage]) -> str:
    """Generate markdown export from wiki pages."""
    markdown_lines = []
    
    for page in pages:
        # Add page title as header
        markdown_lines.append(f"# {page.title}")
        markdown_lines.append("")
        
        # Add page content
        markdown_lines.append(page.content)
        markdown_lines.append("")
        
        # Add metadata if available
        if page.filePaths:
            markdown_lines.append("## Related Files")
            for file_path in page.filePaths:
                markdown_lines.append(f"- {file_path}")
            markdown_lines.append("")
        
        if page.relatedPages:
            markdown_lines.append("## Related Pages")
            for related_page in page.relatedPages:
                markdown_lines.append(f"- {related_page}")
            markdown_lines.append("")
        
        # Add separator between pages
        markdown_lines.append("---")
        markdown_lines.append("")
    
    return "\n".join(markdown_lines)

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
projects_router = APIRouter()


# Authentication routes
@auth_router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Check if authentication is required for the wiki."""
    config = get_config()
    return AuthStatusResponse(auth_required=config.wiki_auth_mode)


@auth_router.post("/validate", response_model=AuthValidationResponse)
async def validate_auth_code(request: AuthorizationConfig):
    """Check authorization code."""
    config = get_config()
    return AuthValidationResponse(success=config.wiki_auth_code == request.code)


# Language configuration route
@auth_router.get("/lang/config", response_model=LanguageConfigResponse)
async def get_lang_config():
    """Get language configuration."""
    lang_config = configs.get("lang", {})
    return LanguageConfigResponse(
        supported_languages=lang_config.get('supported_languages', {}),
        default=lang_config.get('default', 'en')
    )


# JWT-based authentication endpoints
@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT tokens."""
    try:
        config = get_config()
        
        # For now, use simple username/password check
        # In production, implement proper user management with password hashing
        if config.wiki_auth_mode:
            # Simple validation using auth code as password
            if request.password == config.wiki_auth_code:
                user_id = request.username or "default_user"
                
                # Generate JWT tokens
                access_token, refresh_token = jwt_service.generate_tokens(
                    user_id=user_id,
                    additional_claims={
                        "username": request.username,
                        "auth_method": "basic"
                    }
                )
                
                return LoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=30 * 60,  # 30 minutes
                    user_id=user_id
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
        else:
            # If auth not required, create session for any user
            user_id = request.username or "anonymous_user"
            access_token, refresh_token = jwt_service.generate_tokens(
                user_id=user_id,
                additional_claims={
                    "username": request.username,
                    "auth_method": "anonymous"
                }
            )
            
            return LoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=30 * 60,
                user_id=user_id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        # Validate refresh token and get new access token
        new_access_token = jwt_service.refresh_access_token(request.refresh_token)
        
        if not new_access_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token"
            )
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=30 * 60  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@auth_router.post("/logout")
async def logout(request: Request, logout_request: Optional[LogoutRequest] = None):
    """Logout user and revoke tokens."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                scheme, token = auth_header.split(" ", 1)
                if scheme.lower() == "bearer":
                    jwt_service.revoke_token(token)
            except ValueError:
                pass  # Invalid header format, ignore
        
        # Revoke refresh token if provided
        if logout_request and logout_request.refresh_token:
            jwt_service.revoke_token(logout_request.refresh_token)
        
        # Revoke all tokens for user if requested
        if logout_request and logout_request.revoke_all:
            # Get user ID from current token
            if auth_header:
                try:
                    _, token = auth_header.split(" ", 1)
                    token_info = jwt_service.get_token_info(token)
                    if token_info and token_info.get('user_id'):
                        jwt_service.revoke_user_tokens(token_info['user_id'])
                except ValueError:
                    pass
        
        # Clean up expired tokens
        jwt_service.cleanup_expired_tokens()
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@auth_router.get("/token/info", response_model=TokenInfoResponse)
async def get_token_info(request: Request):
    """Get information about the current token."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Authorization header required"
            )
        
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Bearer token required"
                )
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format"
            )
        
        # Get token information
        token_info = jwt_service.get_token_info(token)
        if not token_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        
        return TokenInfoResponse(
            user_id=token_info['user_id'],
            token_type=token_info['type'],
            issued_at=token_info['issued_at'],
            expires_at=token_info['expires_at'],
            is_expired=token_info['is_expired'],
            is_revoked=token_info['is_revoked'],
            jti=token_info['jti']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting token info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get token info")


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


# Wiki routes
@wiki_router.post("/generate")
async def generate_wiki(request: WikiGenerationRequest):
    """Generate wiki documentation for a repository with caching and performance optimization."""
    start_time = time.time()
    logger.info(f"Starting wiki generation for {request.repo_url}")
    
    try:
        # Parse repo URL to extract owner and repo
        repo_parts = request.repo_url.replace("https://", "").replace("http://", "").split("/")
        if len(repo_parts) >= 3:
            owner = repo_parts[1]
            repo = repo_parts[2]
        else:
            # Fallback for invalid URLs
            owner = "unknown" 
            repo = request.repo_url.replace("/", "_")
        
        repo_type = request.repo_type or "github"
        language = request.language or "en"
        
        # Check for existing cache first
        logger.info(f"Checking cache for {owner}/{repo} ({repo_type}, {language})")
        cache_path = get_wiki_cache_path(owner, repo, repo_type, language)
        
        if os.path.exists(cache_path):
            logger.info(f"Cache found at {cache_path}, loading cached wiki")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is less than 24 hours old
                cached_at = datetime.fromisoformat(cached_data.get("cached_at", "1970-01-01"))
                cache_age = datetime.utcnow() - cached_at
                
                if cache_age.total_seconds() < 86400:  # 24 hours
                    logger.info(f"Using cached wiki data (age: {cache_age})")
                    return {
                        "wiki_structure": cached_data.get("wiki_structure"),
                        "status": "success",
                        "provider": cached_data.get("provider", "google"),
                        "model": cached_data.get("model", "gemini-2.0-flash-exp"),
                        "cached": True,
                        "cache_age_hours": round(cache_age.total_seconds() / 3600, 2)
                    }
                else:
                    logger.info(f"Cache expired (age: {cache_age}), regenerating wiki")
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}, generating new wiki")
        
        # Use advanced WikiGenerator for comprehensive analysis
        if gemini_model:
            logger.info("Using advanced WikiGenerator for comprehensive repository analysis")
            
            # Import and use the advanced WikiGenerator
            from ..utils.wiki_generator import WikiGenerator
            from ..utils.data_pipeline import download_repo
            import tempfile
            import shutil
            
            # Create temporary directory for repo download
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Download repository for analysis
                    logger.info(f"Downloading repository {request.repo_url} to {temp_dir}")
                    repo_path = download_repo(
                        request.repo_url, 
                        temp_dir,
                        repo_type,
                        None  # access_token - can be added later if needed
                    )
                    
                    logger.info(f"Repository downloaded to {repo_path}")
                    
                    # Initialize WikiGenerator
                    wiki_generator = WikiGenerator(
                        provider=request.provider or "google",
                        model=request.model or "gemini-2.0-flash-exp"
                    )
                    
                    # Generate comprehensive wiki structure
                    logger.info("Generating comprehensive wiki structure")
                    wiki_structure = wiki_generator.generate_wiki_structure(
                        repo_path,
                        request.repo_url,
                        language
                    )
                    
                    logger.info(f"Wiki structure generated with {len(wiki_structure.get('pages', []))} pages")
                    
                except Exception as e:
                    logger.warning(f"Advanced wiki generation failed: {e}, falling back to basic generation")
                    # Fallback to basic generation if download/analysis fails
                    wiki_structure = await _generate_basic_wiki(request, gemini_model)
            
            # Save to both cache systems
            try:
                # Save to wikicache
                cache_data = {
                    "wiki_structure": wiki_structure,
                    "generated_pages": {page["id"]: page for page in wiki_structure.get("pages", [])},
                    "repo": {
                        "owner": owner,
                        "repo": repo,
                        "type": repo_type,
                        "url": request.repo_url
                    },
                    "provider": request.provider or "google",
                    "model": request.model or "gemini-2.0-flash-exp",
                    "cached_at": datetime.utcnow().isoformat()
                }
                
                # Ensure cache directory exists
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                
                # Save to wikicache
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Wiki cache saved to {cache_path}")
                
                # Also save to project storage for compatibility
                from ..utils.project_storage import ProjectStorage
                storage = ProjectStorage()
                
                generated_pages = {page["id"]: page for page in wiki_structure.get("pages", [])}
                
                project_id = storage.save_project(
                    owner=owner,
                    repo=repo,
                    repo_type=repo_type,
                    language=language,
                    wiki_structure=wiki_structure,
                    generated_pages=generated_pages,
                    provider=request.provider or "google",
                    model=request.model or "gemini-2.0-flash-exp"
                )
                
                logger.info(f"Project saved to storage with ID: {project_id}")
                
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
            
            generation_time = time.time() - start_time
            logger.info(f"Wiki generation completed in {generation_time:.2f} seconds")
            
            return {
                "wiki_structure": wiki_structure,
                "status": "success", 
                "provider": request.provider or "google",
                "model": request.model or "gemini-2.0-flash-exp",
                "cached": False,
                "generation_time_seconds": round(generation_time, 2)
            }
        else:
            return {
                "status": "error",
                "message": "Wiki generation requires Google API key configuration."
            }
    except Exception as e:
        generation_time = time.time() - start_time
        logger.error(f"Error in wiki generation after {generation_time:.2f}s: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_basic_wiki(request: WikiGenerationRequest, gemini_model) -> dict:
    """Fallback basic wiki generation when advanced generation fails."""
    logger.info("Using basic wiki generation fallback")
    
    wiki_prompt = f"""
    Generate comprehensive wiki documentation for repository: {request.repo_url}
    Language: {request.language}
    
    Create structured documentation including:
    1. Project overview and description
    2. Installation and setup instructions
    3. Architecture overview
    4. API documentation
    5. Usage examples
    6. Contributing guidelines
    7. FAQ section
    
    Format the output in a clear, well-structured wiki format.
    """
    
    response = gemini_model.generate_content(wiki_prompt)
    
    # Create a basic wiki structure
    return {
        "id": f"wiki_{request.repo_url.replace('/', '_')}",
        "title": f"Wiki for {request.repo_url}",
        "description": "Auto-generated wiki documentation",
        "pages": [
            {
                "id": "overview",
                "title": "Overview",
                "content": response.text,
                "filePaths": [],
                "importance": "high",
                "relatedPages": []
            }
        ],
        "sections": [],
        "rootSections": ["overview"],
        "generated_at": datetime.utcnow().isoformat(),
        "language": request.language or "en"
    }


@wiki_router.post("/cache")
async def save_wiki_cache(request: WikiCacheRequest):
    """Save wiki cache data to the file system."""
    try:
        cache_path = get_wiki_cache_path(
            request.repo.owner, 
            request.repo.repo, 
            request.repo.type, 
            request.language
        )
        
        logger.info(f"Attempting to save wiki cache. Path: {cache_path}")
        
        # Create cache data structure
        cache_data = {
            "wiki_structure": request.wiki_structure.dict(),
            "generated_pages": {k: v.dict() for k, v in request.generated_pages.items()},
            "repo": request.repo.dict(),
            "provider": request.provider,
            "model": request.model,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        # Save to file
        logger.info(f"Writing cache file to: {cache_path}")
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Wiki cache successfully saved to {cache_path}")
        return {"message": "Wiki cache saved successfully", "cache_path": cache_path}
        
    except IOError as e:
        logger.error(f"IOError saving wiki cache to {cache_path}: {e.strerror} (errno: {e.errno})", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save wiki cache: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error saving wiki cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save wiki cache: {str(e)}")


@wiki_router.post("/export")
async def export_wiki(request: WikiExportRequest):
    """Export wiki pages in the specified format (markdown or json)."""
    try:
        logger.info(f"Exporting wiki for {request.repo_url} in {request.format} format")
        
        if request.format == "markdown":
            # Export as markdown
            markdown_content = generate_markdown_export(request.pages)
            return {
                "format": "markdown",
                "content": markdown_content,
                "repo_url": request.repo_url,
                "exported_at": datetime.utcnow().isoformat(),
                "page_count": len(request.pages)
            }
        elif request.format == "json":
            # Export as JSON
            json_content = {
                "repo_url": request.repo_url,
                "pages": [page.dict() for page in request.pages],
                "exported_at": datetime.utcnow().isoformat(),
                "page_count": len(request.pages)
            }
            return {
                "format": "json",
                "content": json_content,
                "repo_url": request.repo_url,
                "exported_at": datetime.utcnow().isoformat(),
                "page_count": len(request.pages)
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {request.format}")
            
    except Exception as e:
        logger.error(f"Error exporting wiki: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@wiki_router.get("/cache")
async def get_cached_wiki(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    repo_type: str = Query("github", description="Repository type"),
    language: str = Query("en", description="Language")
):
    """Retrieve cached wiki data for a repository."""
    try:
        logger.info(f"Attempting to retrieve wiki cache for {owner}/{repo} ({repo_type}), lang: {language}")
        
        cache_path = get_wiki_cache_path(owner, repo, repo_type, language)
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            logger.info(f"Wiki cache found and loaded from {cache_path}")
            return cache_data
        else:
            logger.info(f"Wiki cache not found for {owner}/{repo} ({repo_type}), lang: {language}")
            return None
            
    except Exception as e:
        logger.error(f"Error reading wiki cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read wiki cache: {str(e)}")


@wiki_router.delete("/cache")
async def delete_cached_wiki(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    repo_type: str = Query("github", description="Repository type"),
    language: str = Query("en", description="Language")
):
    """Delete a specific wiki cache from the file system."""
    try:
        logger.info(f"Attempting to delete wiki cache for {owner}/{repo} ({repo_type}), lang: {language}")
        
        cache_path = get_wiki_cache_path(owner, repo, repo_type, language)
        
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info(f"Successfully deleted wiki cache: {cache_path}")
            return {"message": f"Wiki cache for {owner}/{repo} ({language}) deleted successfully"}
        else:
            logger.warning(f"Wiki cache not found, cannot delete: {cache_path}")
            raise HTTPException(status_code=404, detail="Wiki cache not found")
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Wiki cache not found")
    except Exception as e:
        logger.error(f"Error deleting wiki cache {cache_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete wiki cache: {str(e)}")


@wiki_router.get("/projects")
async def list_processed_projects():
    """List all processed projects found in the wiki cache directory."""
    try:
        logger.info(f"Scanning for project cache files in: {WIKI_CACHE_DIR}")
        
        projects = []
        
        if os.path.exists(WIKI_CACHE_DIR):
            for filename in os.listdir(WIKI_CACHE_DIR):
                if filename.startswith("grantha_cache_") and filename.endswith(".json"):
                    try:
                        # Parse filename: grantha_cache_{repo_type}_{owner}_{repo}_{language}.json
                        parts = filename.replace("grantha_cache_", "").replace(".json", "").split('_')
                        if len(parts) >= 4:
                            repo_type = parts[0]
                            owner = parts[1]
                            repo = parts[2]
                            language = '_'.join(parts[3:])  # Handle languages with underscores
                            
                            # Get file modification time
                            file_path = os.path.join(WIKI_CACHE_DIR, filename)
                            stat_info = os.stat(file_path)
                            submitted_at = int(stat_info.st_mtime * 1000)  # Convert to milliseconds
                            
                            project = {
                                "id": filename,
                                "owner": owner,
                                "repo": repo,
                                "name": f"{owner}/{repo}",
                                "repo_type": repo_type,
                                "submittedAt": submitted_at,
                                "language": language
                            }
                            projects.append(project)
                        else:
                            logger.warning(f"Skipping malformed cache filename: {filename}")
                    except Exception as e:
                        logger.warning(f"Error parsing cache filename {filename}: {e}")
        
        logger.info(f"Found {len(projects)} processed projects")
        return projects
        
    except Exception as e:
        logger.error(f"Error listing processed projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list processed projects from server cache.")


# Chat routes
@chat_router.post("/completion")
async def chat_completion(request: ChatRequest):
    """Handle chat completion requests."""
    try:
        # Use Gemini model if available
        if gemini_model:
            # Convert messages to a single prompt
            prompt = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in request.messages
            ])
            
            # Generate response
            response = gemini_model.generate_content(prompt)
            
            return ChatResponse(
                content=response.text,
                role="assistant",
                model=request.model or "gemini-2.0-flash-exp",
                provider=request.provider or "google"
            )
        else:
            # Fallback response if no API key
            return ChatResponse(
                content="Chat API is not configured. Please set up Google API key.",
                role="assistant",
                model="none",
                provider="none"
            )
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/completions/stream")
async def chat_completions_stream(request: ChatStreamRequest):
    """Handle streaming chat completion requests using Server-Sent Events."""
    try:
        logger.info(f"Starting streaming chat completion for {len(request.messages)} messages")
        
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                if gemini_model:
                    # Convert messages to a single prompt
                    prompt = "\n".join([
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                        for msg in request.messages
                    ])
                    
                    logger.info(f"Generating streaming response with Gemini model")
                    
                    # Generate streaming response
                    response = gemini_model.generate_content(
                        prompt,
                        stream=True,
                        generation_config={
                            "temperature": request.temperature or 0.7,
                            "top_p": 0.8,
                            "top_k": 40
                        }
                    )
                    
                    # Stream the response chunks
                    for chunk in response:
                        if chunk.text:
                            # Format as SSE data
                            chunk_data = {
                                "content": chunk.text,
                                "done": False,
                                "model": request.model or "gemini-2.0-flash-exp",
                                "provider": request.provider or "google"
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                            
                            # Add small delay to prevent overwhelming the client
                            await asyncio.sleep(0.01)
                    
                    # Send completion signal
                    completion_data = {
                        "content": "",
                        "done": True,
                        "model": request.model or "gemini-2.0-flash-exp",
                        "provider": request.provider or "google"
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    
                else:
                    # Fallback response if no API key
                    fallback_message = "Chat API is not configured. Please set up Google API key."
                    
                    # Stream the fallback message word by word
                    words = fallback_message.split()
                    for i, word in enumerate(words):
                        chunk_data = {
                            "content": word + (" " if i < len(words) - 1 else ""),
                            "done": False,
                            "model": "none",
                            "provider": "none"
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                        await asyncio.sleep(0.1)  # Slower for fallback
                    
                    # Send completion signal
                    completion_data = {
                        "content": "",
                        "done": True,
                        "model": "none",
                        "provider": "none"
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    
            except Exception as e:
                logger.error(f"Error in streaming generation: {str(e)}")
                # Send error through the stream
                error_data = {
                    "error": str(e),
                    "content": f"Error: {str(e)}",
                    "done": True,
                    "model": request.model or "unknown",
                    "provider": request.provider or "unknown"
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat completions stream: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Research routes
@research_router.post("/deep")
async def deep_research(request: DeepResearchRequest):
    """Perform deep research on a topic."""
    try:
        # Use Gemini model for research if available
        if gemini_model:
            # Create research prompt with context
            research_prompt = f"""
            Research Query: {request.query}
            Repository Context: {request.repo_url}
            Language: {request.language}
            
            Please provide a comprehensive research response covering:
            1. Key insights and findings
            2. Technical details
            3. Best practices and recommendations
            4. Relevant code examples if applicable
            5. Additional resources
            """
            
            response = gemini_model.generate_content(research_prompt)
            
            return {
                "query": request.query,
                "results": response.text,
                "repo_url": request.repo_url,
                "provider": request.provider or "google",
                "model": request.model or "gemini-2.0-flash-exp",
                "language": request.language,
                "status": "success"
            }
        else:
            return {
                "query": request.query,
                "results": "Research API requires Google API key configuration.",
                "repo_url": request.repo_url,
                "provider": "none",
                "model": "none",
                "status": "error"
            }
    except Exception as e:
        logger.error(f"Error in deep research: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Simple routes
@simple_router.post("/chat", response_model=SimpleResponse)
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


# Project management routes
@projects_router.get("/processed_projects")
async def get_processed_projects():
    """Get list of all processed projects from cache."""
    try:
        # Import the project storage utility
        from ..utils.project_storage import ProjectStorage
        
        storage = ProjectStorage()
        projects = storage.list_projects()
        
        return projects
        
    except Exception as e:
        logger.error(f"Error fetching processed projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch processed projects: {str(e)}")


@projects_router.delete("/wiki_cache")
async def delete_wiki_cache(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    repo_type: str = Query(..., description="Repository type"),
    language: str = Query(..., description="Language")
):
    """Delete a specific project's wiki cache."""
    try:
        # Import the project storage utility
        from ..utils.project_storage import ProjectStorage
        
        storage = ProjectStorage()
        result = storage.delete_project(owner, repo, repo_type, language)
        
        if result:
            return {"message": "Project cache deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Project not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project cache: {str(e)}")


@projects_router.post("/processed_projects")
async def save_processed_project(request: Dict[str, Any]):
    """Save a processed project entry."""
    try:
        # Import the project storage utility
        from ..utils.project_storage import ProjectStorage
        
        storage = ProjectStorage()
        project_id = storage.save_project(
            owner=request.get("owner", ""),
            repo=request.get("repo", ""),
            repo_type=request.get("repo_type", "github"),
            language=request.get("language", "en"),
            wiki_structure=request.get("wiki_structure"),
            generated_pages=request.get("generated_pages", {}),
            provider=request.get("provider", "google"),
            model=request.get("model", "")
        )
        
        return {"id": project_id, "message": "Project saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving processed project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save processed project: {str(e)}")