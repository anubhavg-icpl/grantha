# Grantha API Reference

## Base Information

- **Base URL**: `http://localhost:8001` (default)
- **API Version**: 1.0.0
- **Protocol**: HTTP/HTTPS with WebSocket support
- **Content-Type**: `application/json`

## Authentication

Authentication is optional and controlled by environment variables:

```bash
GRANTHA_AUTH_MODE=true
GRANTHA_AUTH_CODE=your-secret-code
```

When authentication is enabled, include the authorization code in requests:

```http
POST /auth/validate
Content-Type: application/json

{
  "code": "your-secret-code"
}
```

## Core Endpoints

### Health Check

#### `GET /health`

Check system health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-08-25T10:30:00Z",
  "providers": {
    "google": "available",
    "openai": "available"
  }
}
```

#### `GET /`

API welcome message and basic information.

**Response:**
```json
{
  "message": "Welcome to ग्रंथ (Grantha) API",
  "version": "1.0.0",
  "description": "Knowledge management and documentation API powered by AI"
}
```

## Configuration Endpoints

### Get Model Configuration

#### `GET /models/config`

Retrieve available models and providers configuration.

**Response:**
```json
{
  "providers": {
    "google": {
      "id": "google",
      "name": "Google Gemini",
      "models": [
        {
          "id": "gemini-1.5-pro",
          "name": "Gemini 1.5 Pro",
          "description": "Most capable model for complex tasks"
        },
        {
          "id": "gemini-1.5-flash",
          "name": "Gemini 1.5 Flash",
          "description": "Fast and efficient model"
        }
      ]
    },
    "openai": {
      "id": "openai",
      "name": "OpenAI",
      "models": [
        {
          "id": "gpt-4",
          "name": "GPT-4",
          "description": "Most capable GPT model"
        }
      ]
    }
  },
  "defaultProvider": "google"
}
```

### Get Language Configuration

#### `GET /lang/config`

Get supported languages configuration.

**Response:**
```json
{
  "supported_languages": {
    "en": "English",
    "ja": "Japanese (日本語)",
    "zh": "Mandarin Chinese (中文)",
    "zh-tw": "Traditional Chinese (繁體中文)",
    "es": "Spanish (Español)",
    "kr": "Korean (한국어)",
    "vi": "Vietnamese (Tiếng Việt)",
    "pt-br": "Brazilian Portuguese (Português Brasileiro)",
    "fr": "Français (French)",
    "ru": "Русский (Russian)"
  },
  "default": "en"
}
```

## Authentication Endpoints

### Get Auth Status

#### `GET /auth/status`

Check authentication status and requirements.

**Response:**
```json
{
  "auth_required": true,
  "authenticated": false
}
```

### Validate Authentication

#### `POST /auth/validate`

Validate authentication code.

**Request Body:**
```json
{
  "code": "your-authentication-code"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Authentication successful"
}
```

## Wiki Operations

### Generate Wiki Structure

#### `POST /api/wiki/generate`

Generate comprehensive wiki structure from repository analysis.

**Request Body:**
```json
{
  "repoInfo": {
    "owner": "username",
    "repo": "repository-name",
    "type": "github",
    "token": "optional-github-token",
    "localPath": "/path/to/local/repo",
    "repoUrl": "https://github.com/username/repository-name"
  },
  "language": "en",
  "provider": "google",
  "model": "gemini-1.5-pro"
}
```

**Response:**
```json
{
  "id": "wiki-12345",
  "title": "Repository Documentation",
  "description": "Comprehensive documentation for the repository",
  "pages": [
    {
      "id": "overview",
      "title": "Project Overview",
      "content": "# Project Overview\n\nThis project is...",
      "filePaths": ["README.md", "src/main.py"],
      "importance": "high",
      "relatedPages": ["architecture", "setup"]
    }
  ],
  "sections": [
    {
      "id": "getting-started",
      "title": "Getting Started",
      "pages": ["overview", "installation"],
      "subsections": []
    }
  ],
  "rootSections": ["getting-started", "architecture"]
}
```

### Wiki Cache Operations

#### `GET /api/wiki_cache`

Retrieve cached wiki data.

**Query Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `repo_type` (string, required): Repository type (e.g., "github")
- `language` (string, required): Language code

**Response:**
```json
{
  "wiki_structure": {
    "id": "cached-wiki-123",
    "title": "Cached Wiki",
    "description": "Previously generated wiki structure",
    "pages": [...],
    "sections": [...]
  }
}
```

#### `POST /api/wiki_cache`

Store wiki structure in cache.

**Request Body:**
```json
{
  "owner": "username",
  "repo": "repository",
  "repo_type": "github",
  "language": "en",
  "wiki_structure": {
    "id": "wiki-123",
    "title": "Wiki Title",
    "description": "Wiki description",
    "pages": [...],
    "sections": [...]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Wiki cache stored successfully"
}
```

#### `DELETE /api/wiki_cache`

Clear wiki cache.

**Query Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `repo_type` (string, required): Repository type
- `language` (string, required): Language code

**Response:**
```json
{
  "success": true,
  "message": "Wiki cache cleared successfully"
}
```

### Export Wiki

#### `POST /export/wiki`

Export wiki in various formats.

**Request Body:**
```json
{
  "repo_url": "https://github.com/username/repo",
  "pages": [...],
  "format": "markdown"
}
```

**Supported formats:**
- `markdown` - Export as Markdown files
- `json` - Export as JSON structure

**Response:**
- Content-Type varies based on format
- Markdown: `text/markdown`
- JSON: `application/json`

## Research Operations

### Deep Research

#### `POST /api/research/deep`

Conduct comprehensive research with streaming updates.

**Request Body:**
```json
{
  "query": "Explain machine learning algorithms",
  "context": "Educational content for beginners",
  "depth": "comprehensive",
  "provider": "google",
  "model": "gemini-1.5-pro"
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"type": "progress", "stage": "initial_research", "content": "Starting research..."}

data: {"type": "progress", "stage": "analysis", "content": "Analyzing sources..."}

data: {"type": "result", "content": "# Machine Learning Algorithms\n\n..."}

data: {"type": "complete", "final_result": "..."}
```

## Chat Operations

### Streaming Chat Completions

#### `POST /chat/completions/stream`

Generate streaming chat completions.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Explain Python decorators"
    }
  ],
  "model": "gpt-4",
  "provider": "openai",
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"choices": [{"delta": {"content": "Python"}}]}

data: {"choices": [{"delta": {"content": " decorators"}}]}

data: {"choices": [{"delta": {"content": " are"}}]}

data: [DONE]
```

## Repository Operations

### Get Repository Structure

#### `GET /local_repo/structure`

Analyze and retrieve local repository structure.

**Query Parameters:**
- `path` (string, required): Path to local repository

**Response:**
```json
{
  "path": "/path/to/repo",
  "structure": {
    "files": [
      {
        "name": "README.md",
        "type": "file",
        "size": 1024,
        "language": "markdown"
      },
      {
        "name": "src",
        "type": "directory",
        "children": [...]
      }
    ],
    "stats": {
      "total_files": 42,
      "languages": {
        "python": 25,
        "javascript": 10,
        "markdown": 7
      }
    }
  }
}
```

### Get Processed Projects

#### `GET /api/processed_projects`

List previously processed projects.

**Response:**
```json
[
  {
    "id": "project1.json",
    "owner": "username",
    "repo": "repository",
    "name": "username/repository",
    "repo_type": "github",
    "submittedAt": 1692960000,
    "language": "python"
  }
]
```

## WebSocket Endpoints

### Chat WebSocket

#### `WS /ws/chat`

Real-time chat interface with WebSocket.

**Message Format:**
```json
{
  "type": "message",
  "content": "Your message here",
  "provider": "google",
  "model": "gemini-1.5-pro"
}
```

**Response Format:**
```json
{
  "type": "response",
  "content": "AI response",
  "timestamp": "2025-08-25T10:30:00Z"
}
```

## Data Models

### WikiPage
```typescript
interface WikiPage {
  id: string;
  title: string;
  content: string;
  filePaths: string[];
  importance: "high" | "medium" | "low";
  relatedPages: string[];
}
```

### WikiSection
```typescript
interface WikiSection {
  id: string;
  title: string;
  pages: string[];
  subsections?: string[];
}
```

### WikiStructure
```typescript
interface WikiStructure {
  id: string;
  title: string;
  description: string;
  pages: WikiPage[];
  sections?: WikiSection[];
  rootSections?: string[];
}
```

### RepoInfo
```typescript
interface RepoInfo {
  owner: string;
  repo: string;
  type: string;
  token?: string;
  localPath?: string;
  repoUrl?: string;
}
```

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error description",
  "type": "error_type",
  "code": 400
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Invalid authentication code |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

## Rate Limiting

Currently no rate limiting is implemented, but consider implementing:
- Request rate limits per IP
- API key-based quotas
- Provider-specific rate limits

## SDKs and Examples

### Python Example
```python
import requests
import json

# Generate wiki structure
response = requests.post('http://localhost:8001/api/wiki/generate', 
  json={
    "repoInfo": {
      "owner": "username",
      "repo": "repository",
      "type": "github"
    },
    "language": "en"
  }
)

wiki_structure = response.json()
print(json.dumps(wiki_structure, indent=2))
```

### JavaScript Example
```javascript
// Streaming chat completion
const response = await fetch('http://localhost:8001/chat/completions/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'Hello!' }],
    provider: 'google',
    stream: true
  })
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = new TextDecoder().decode(value);
  console.log(chunk);
}
```

### cURL Examples
```bash
# Health check
curl http://localhost:8001/health

# Generate wiki
curl -X POST http://localhost:8001/api/wiki/generate \
  -H "Content-Type: application/json" \
  -d '{
    "repoInfo": {
      "owner": "username",
      "repo": "repository",
      "type": "github"
    },
    "language": "en"
  }'

# Streaming chat
curl -N -X POST http://localhost:8001/chat/completions/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

---

*This API reference provides comprehensive documentation for all Grantha endpoints. For more examples and use cases, refer to the main documentation.*