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
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


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