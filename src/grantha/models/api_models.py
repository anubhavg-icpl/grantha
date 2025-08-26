"""Pydantic models for the Grantha API."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class WikiPage(BaseModel):
    """Model for a wiki page."""
    id: str
    title: str
    content: str
    filePaths: List[str]
    importance: str  # Should ideally be Literal['high', 'medium', 'low']
    relatedPages: List[str]


class ProcessedProjectEntry(BaseModel):
    """Model for processed project entries."""
    id: str  # Filename
    owner: str
    repo: str
    name: str  # owner/repo
    repo_type: str  # Renamed from type to repo_type for clarity with existing models
    submittedAt: int  # Timestamp
    language: str  # Extracted from filename


class RepoInfo(BaseModel):
    """Model for repository information."""
    owner: str
    repo: str
    type: str
    token: Optional[str] = None
    localPath: Optional[str] = None
    repoUrl: Optional[str] = None


class WikiSection(BaseModel):
    """Model for the wiki sections."""
    id: str
    title: str
    pages: List[str]
    subsections: Optional[List[str]] = None


class WikiStructureModel(BaseModel):
    """Model for the overall wiki structure."""
    id: str
    title: str
    description: str
    pages: List[WikiPage]
    sections: Optional[List[WikiSection]] = None
    rootSections: Optional[List[str]] = None


class WikiCacheData(BaseModel):
    """Model for the data to be stored in the wiki cache."""
    wiki_structure: WikiStructureModel
    generated_pages: Dict[str, WikiPage]
    repo_url: Optional[str] = None  # compatible for old cache
    repo: Optional[RepoInfo] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class WikiCacheRequest(BaseModel):
    """Model for the request body when saving wiki cache."""
    repo: RepoInfo
    language: str
    wiki_structure: WikiStructureModel
    generated_pages: Dict[str, WikiPage]
    provider: str
    model: str


class WikiExportRequest(BaseModel):
    """Model for requesting a wiki export."""
    repo_url: str = Field(..., description="URL of the repository")
    pages: List[WikiPage] = Field(..., description="List of wiki pages to export")
    format: Literal["markdown", "json"] = Field(..., description="Export format (markdown or json)")


class Model(BaseModel):
    """Model for LLM model configuration."""
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Display name for the model")


class Provider(BaseModel):
    """Model for LLM provider configuration."""
    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Display name for the provider")
    models: List[Model] = Field(..., description="List of available models for this provider")
    supportsCustomModel: Optional[bool] = Field(False, description="Whether this provider supports custom models")


class ModelConfig(BaseModel):
    """Model for the entire model configuration."""
    providers: List[Provider] = Field(..., description="List of available model providers")
    defaultProvider: str = Field(..., description="ID of the default provider")


class WikiGenerationRequest(BaseModel):
    """Model for requesting wiki generation with Mermaid diagrams."""
    repo_url: str = Field(..., description="URL of the repository")
    language: str = Field("en", description="Language for wiki content")
    provider: str = Field("google", description="Model provider")
    model: Optional[str] = Field(None, description="Specific model to use")
    token: Optional[str] = Field(None, description="Access token for private repositories")
    repo_type: str = Field("github", description="Repository type")


class DeepResearchRequest(BaseModel):
    """Model for requesting deep research on a topic."""
    query: str = Field(..., description="Research question")
    repo_url: str = Field(..., description="Repository URL for context")
    language: str = Field("en", description="Language for responses")
    provider: str = Field("google", description="Model provider")
    model: Optional[str] = Field(None, description="Specific model to use")
    token: Optional[str] = Field(None, description="Access token for private repositories")
    repo_type: str = Field("github", description="Repository type")


class AuthorizationConfig(BaseModel):
    """Model for authorization configuration."""
    code: str = Field(..., description="Authorization code")


class LoginRequest(BaseModel):
    """Model for login requests."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(False, description="Whether to extend session duration")


class LoginResponse(BaseModel):
    """Model for login responses."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user_id: str = Field(..., description="User ID")


class RefreshTokenRequest(BaseModel):
    """Model for refresh token requests."""
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Model for refresh token responses."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Model for logout requests."""
    refresh_token: Optional[str] = Field(None, description="JWT refresh token to revoke")
    revoke_all: bool = Field(False, description="Whether to revoke all user tokens")


class TokenInfoResponse(BaseModel):
    """Model for token information responses."""
    user_id: str = Field(..., description="User ID")
    token_type: str = Field(..., description="Token type (access/refresh)")
    issued_at: int = Field(..., description="Token issued timestamp")
    expires_at: int = Field(..., description="Token expiration timestamp")
    is_expired: bool = Field(..., description="Whether token is expired")
    is_revoked: bool = Field(..., description="Whether token is revoked")
    jti: str = Field(..., description="JWT ID (unique token identifier)")


class ChatRequest(BaseModel):
    """Model for chat requests."""
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    provider: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Model for chat responses."""
    content: str
    model: str
    provider: str
    role: str = "assistant"
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class ChatStreamRequest(BaseModel):
    """Model for streaming chat requests."""
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = True


class SimpleRequest(BaseModel):
    """Model for simple chat requests."""
    user_query: str
    repo_url: Optional[str] = None
    provider: str = Field("google", description="Model provider")
    model: Optional[str] = Field(None, description="Specific model to use")
    language: str = Field("en", description="Language for responses")
    token: Optional[str] = Field(None, description="Access token for private repositories")
    repo_type: str = Field("github", description="Repository type")


class RAGRequest(BaseModel):
    """Model for RAG (Retrieval-Augmented Generation) requests."""
    query: str = Field(..., description="Query string")
    repo_url: str = Field(..., description="Repository URL")
    provider: str = Field("google", description="Model provider")
    model: Optional[str] = Field(None, description="Specific model to use")
    language: str = Field("en", description="Language for responses")
    token: Optional[str] = Field(None, description="Access token for private repositories")
    repo_type: str = Field("github", description="Repository type")
    k: int = Field(5, description="Number of relevant documents to retrieve")


# Response Models

class AuthStatusResponse(BaseModel):
    """Response model for auth status."""
    auth_required: bool = Field(..., description="Whether authentication is required")


class AuthValidationResponse(BaseModel):
    """Response model for auth code validation."""
    success: bool = Field(..., description="Whether the authorization code is valid")


class LanguageConfigResponse(BaseModel):
    """Response model for language configuration."""
    supported_languages: Dict[str, str] = Field(..., description="Supported languages with codes and names")
    default: str = Field(..., description="Default language code")


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    content: str = Field(..., description="The generated response content")
    model: str = Field(..., description="Model used for generation")
    provider: str = Field(..., description="Provider used for generation")
    role: str = Field("assistant", description="Role of the response")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason for completion finish")


class SimpleResponse(BaseModel):
    """Response model for simple chat."""
    message: str = Field(..., description="The generated response message")
    provider: str = Field(..., description="Provider used for generation")
    model: str = Field(..., description="Model used for generation")
    status: str = Field("success", description="Response status")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    status: str = Field(..., description="System status")
    cache: Dict[str, Any] = Field(..., description="Cache metrics and configuration")
    middleware: Dict[str, str] = Field(..., description="Middleware status")
    performance: Dict[str, str] = Field(..., description="Performance metrics")


class ProjectListResponse(BaseModel):
    """Response model for processed projects list."""
    projects: List[Dict[str, Any]] = Field(..., description="List of processed projects")


class WikiGenerationResponse(BaseModel):
    """Response model for wiki generation."""
    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    wiki_structure: Optional[Dict[str, Any]] = Field(None, description="Generated wiki structure")
    cache_path: Optional[str] = Field(None, description="Path to cached wiki data")