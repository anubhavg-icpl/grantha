# Grantha Development Guide

## Prerequisites

- Python 3.12 or higher
- Git
- Virtual environment tool (venv, conda, etc.)
- API keys for AI providers (at minimum Google Gemini)

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/anubhavg-icpl/grantha.git
cd grantha
```

### 2. Create Virtual Environment

```bash
# Using Python venv
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install in development mode with all dependencies
pip install -e .

# Or install from requirements if available
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Required - Google Gemini API key
GOOGLE_API_KEY=your_google_api_key_here

# Optional - Additional providers
OPENAI_API_KEY=your_openai_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# AWS Bedrock (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Authentication (optional)
GRANTHA_AUTH_MODE=false
GRANTHA_AUTH_CODE=your_secret_code

# Configuration directory (optional)
GRANTHA_CONFIG_DIR=/path/to/custom/config

# Development settings
NODE_ENV=development
PORT=8001
```

### 5. Configuration Files

The system uses JSON configuration files in `api/config/`. Create or customize:

#### `api/config/generator.json`
```json
{
  "default_provider": "google",
  "providers": {
    "google": {
      "client_class": "GoogleGenAIClient",
      "default_model": "gemini-1.5-flash",
      "models": {
        "gemini-1.5-pro": {
          "temperature": 0.7,
          "max_output_tokens": 8192
        },
        "gemini-1.5-flash": {
          "temperature": 0.7,
          "max_output_tokens": 8192
        }
      }
    },
    "openai": {
      "client_class": "OpenAIClient",
      "default_model": "gpt-4",
      "models": {
        "gpt-4": {
          "temperature": 0.7,
          "max_tokens": 4096
        },
        "gpt-3.5-turbo": {
          "temperature": 0.7,
          "max_tokens": 4096
        }
      }
    }
  }
}
```

#### `api/config/embedder.json`
```json
{
  "embedder": {
    "client_class": "OpenAIClient",
    "model_kwargs": {
      "model": "text-embedding-3-small",
      "dimensions": 1536
    }
  },
  "text_splitter": {
    "split_by": "word",
    "split_length": 400,
    "split_overlap": 200
  }
}
```

### 6. Run Development Server

```bash
python -m api.main
```

The server will start on `http://localhost:8001` with hot reloading enabled.

## Development Workflow

### Project Structure

```
grantha/
├── api/                     # Main API package
│   ├── __init__.py
│   ├── main.py             # Application entry point
│   ├── api.py              # FastAPI routes and handlers
│   ├── config.py           # Configuration management
│   ├── logging_config.py   # Logging setup
│   │
│   ├── config/             # JSON configuration files
│   │   ├── generator.json  # LLM provider configs
│   │   ├── embedder.json   # Embedding configs
│   │   ├── repo.json       # Repository settings
│   │   └── lang.json       # Language support
│   │
│   ├── tools/              # Utility tools
│   │   └── embedder.py     # Embedding utilities
│   │
│   ├── *_client.py         # AI provider clients
│   ├── wiki_generator.py   # Wiki generation service
│   ├── deep_research.py    # Research service
│   ├── rag.py              # RAG implementation
│   ├── simple_chat.py      # Chat completions
│   ├── websocket_wiki.py   # WebSocket handlers
│   ├── data_pipeline.py    # Data processing
│   └── prompts.py          # Prompt templates
│
├── docs/                   # Documentation
├── venv/                   # Virtual environment
├── .env                    # Environment variables
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Project configuration
├── pytest.ini             # Test configuration
└── test_api.py             # API tests
```

### Code Style and Standards

#### Python Style Guide
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and returns
- Document classes and functions with docstrings
- Use meaningful variable and function names

#### Example Function Documentation
```python
async def generate_wiki_structure(request: WikiGenerationRequest) -> WikiStructureModel:
    """
    Generate comprehensive wiki structure from repository analysis.

    Args:
        request (WikiGenerationRequest): Request containing repository info and options

    Returns:
        WikiStructureModel: Generated wiki structure with pages and sections

    Raises:
        HTTPException: If repository analysis fails
        ValueError: If invalid configuration provided
    """
    # Implementation here
    pass
```

#### API Endpoint Documentation
```python
@app.post("/api/wiki/generate", response_model=WikiStructureModel)
async def generate_wiki_structure(request: WikiGenerationRequest):
    """
    Generate comprehensive wiki structure from repository.

    This endpoint analyzes a repository and generates a structured wiki
    with pages, sections, and content organized for documentation.
    """
    pass
```

### Adding New Features

#### 1. Adding a New AI Provider

**Step 1:** Create client class
```python
# api/newprovider_client.py
from typing import Dict, Any, AsyncIterator
import logging

logger = logging.getLogger(__name__)

class NewProviderClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Initialize client

    async def complete(self, messages: list, **kwargs) -> str:
        """Generate completion"""
        # Implementation
        pass

    async def stream_complete(self, messages: list, **kwargs) -> AsyncIterator[str]:
        """Generate streaming completion"""
        # Implementation
        pass
```

**Step 2:** Register in configuration
```python
# api/config.py
from api.newprovider_client import NewProviderClient

CLIENT_CLASSES = {
    # ... existing clients
    "NewProviderClient": NewProviderClient,
}
```

**Step 3:** Add configuration
```json
// api/config/generator.json
{
  "providers": {
    "newprovider": {
      "client_class": "NewProviderClient",
      "default_model": "model-name",
      "models": {
        "model-name": {
          "temperature": 0.7
        }
      }
    }
  }
}
```

#### 2. Adding New API Endpoints

```python
# In api/api.py
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    """Request model for new feature"""
    parameter: str
    options: Dict[str, Any] = {}

class NewFeatureResponse(BaseModel):
    """Response model for new feature"""
    result: str
    metadata: Dict[str, Any]

@app.post("/api/new-feature", response_model=NewFeatureResponse)
async def new_feature_endpoint(request: NewFeatureRequest):
    """
    Description of the new feature endpoint.
    """
    try:
        # Implementation
        result = await process_new_feature(request)
        return NewFeatureResponse(
            result=result,
            metadata={"processed_at": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"Error in new feature: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_api.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=api
```

#### Writing Tests

```python
# test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from api.api import app

client = TestClient(app)

def test_new_feature():
    """Test new feature endpoint"""
    request_data = {
        "parameter": "test_value",
        "options": {"setting": "value"}
    }

    response = client.post("/api/new-feature", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "metadata" in data

@pytest.mark.asyncio
async def test_async_feature():
    """Test async functionality"""
    from api.your_module import your_async_function

    result = await your_async_function("test_input")
    assert result is not None
```

### Debugging

#### Logging Configuration

The system uses structured logging. Configure log levels in development:

```python
# api/logging_config.py
import logging

# Set debug level for development
logging.getLogger("api").setLevel(logging.DEBUG)
logging.getLogger("your_module").setLevel(logging.DEBUG)
```

#### Debug Settings

```bash
# Enable debug mode
export PYTHONPATH="$PYTHONPATH:."
export LOG_LEVEL=DEBUG

# Run with debugging
python -m pdb api/main.py
```

#### VS Code Debug Configuration

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Grantha API",
            "type": "python",
            "request": "launch",
            "module": "api.main",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "LOG_LEVEL": "DEBUG"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

### Database and Storage

#### File System Cache

```python
# Cache management
from api.config import get_adalflow_default_root_path
import os
import json

cache_dir = os.path.join(get_adalflow_default_root_path(), "custom_cache")
os.makedirs(cache_dir, exist_ok=True)

def save_cache(key: str, data: dict):
    cache_file = os.path.join(cache_dir, f"{key}.json")
    with open(cache_file, 'w') as f:
        json.dump(data, f)

def load_cache(key: str) -> dict:
    cache_file = os.path.join(cache_dir, f"{key}.json")
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}
```

### Performance Optimization

#### Async Best Practices

```python
import asyncio
from typing import List

# Good: Concurrent execution
async def process_multiple_requests(requests: List[dict]) -> List[dict]:
    tasks = [process_single_request(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]

# Good: Streaming responses
async def stream_large_data():
    async def generate():
        for chunk in get_data_chunks():
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.01)  # Allow other tasks

    return StreamingResponse(generate(), media_type="text/plain")
```

#### Memory Management

```python
# Good: Process data in chunks
async def process_large_file(file_path: str):
    chunk_size = 8192
    with open(file_path, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            await process_chunk(chunk)

# Good: Cleanup resources
async def process_with_cleanup():
    client = None
    try:
        client = await create_expensive_client()
        result = await client.process()
        return result
    finally:
        if client:
            await client.close()
```

### Common Development Tasks

#### 1. Adding New Configuration Options

```python
# 1. Update JSON schema
# api/config/your_config.json
{
  "new_option": "default_value",
  "complex_option": {
    "nested": "value"
  }
}

# 2. Load in config.py
def load_your_config():
    return load_json_config("your_config.json")

# 3. Use in application
from api.config import configs
new_value = configs.get("new_option", "fallback")
```

#### 2. Implementing Streaming Endpoints

```python
from fastapi.responses import StreamingResponse
import json

@app.post("/api/stream-data")
async def stream_data(request: DataRequest):
    async def generate():
        yield "data: {\"type\": \"start\"}\n\n"

        async for item in process_data_stream(request):
            data = json.dumps({"type": "data", "content": item})
            yield f"data: {data}\n\n"

        yield "data: {\"type\": \"complete\"}\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
```

#### 3. Error Handling Patterns

```python
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def safe_operation(data: dict):
    try:
        # Validate input
        if not data:
            raise ValueError("No data provided")

        # Process
        result = await process_data(data)

        # Validate output
        if not result:
            raise RuntimeError("Processing failed")

        return result

    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal processing error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
```

### Deployment

#### Development Deployment

```bash
# With auto-reload
python -m api.main

# With specific configuration
GRANTHA_CONFIG_DIR=/path/to/config python -m api.main
```

#### Production Deployment

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001

# With environment file
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 --env-file .env
```

#### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "-m", "api.main"]
```

```bash
# Build and run
docker build -t grantha-api .
docker run -p 8001:8001 --env-file .env grantha-api
```

### Monitoring and Maintenance

#### Health Monitoring

```python
# Custom health checks
@app.get("/health/detailed")
async def detailed_health():
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "providers": await check_providers(),
        "disk_space": check_disk_space()
    }

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

#### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time

        logger.info(f"{func.__name__} completed in {duration:.3f}s")
        return result
    return wrapper

@monitor_performance
async def expensive_operation():
    # Implementation
    pass
```

This development guide provides comprehensive information for setting up and developing Grantha. For specific implementation details, refer to the source code and architecture documentation.
