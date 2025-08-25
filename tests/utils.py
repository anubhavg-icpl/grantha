"""
Test utilities and helper functions.
"""

import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data: Dict[Any, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {"content-type": "application/json"}
        self.text = json.dumps(json_data)
        self.content = self.text.encode('utf-8')

    def json(self):
        return self.json_data


class MockStreamingResponse:
    """Mock streaming response for testing."""
    
    def __init__(self, chunks: List[str], status_code: int = 200):
        self.chunks = chunks
        self.status_code = status_code
        self.headers = {"content-type": "text/event-stream"}
    
    def iter_content(self, chunk_size=None):
        for chunk in self.chunks:
            yield chunk.encode('utf-8')


class MockRepositoryBuilder:
    """Helper to build mock repositories for testing."""
    
    def __init__(self):
        self.temp_dir = None
        self.files = {}
        self.directories = []
    
    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
    
    def add_file(self, path: str, content: str):
        """Add a file to the mock repository."""
        if self.temp_dir:
            file_path = Path(self.temp_dir) / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        self.files[path] = content
        return self
    
    def add_directory(self, path: str):
        """Add a directory to the mock repository."""
        if self.temp_dir:
            dir_path = Path(self.temp_dir) / path
            dir_path.mkdir(parents=True, exist_ok=True)
        self.directories.append(path)
        return self
    
    def get_path(self):
        """Get the temporary directory path."""
        return self.temp_dir


def create_sample_python_repo():
    """Create a sample Python repository for testing."""
    return MockRepositoryBuilder().add_file(
        "main.py",
        """
def main():
    '''Main entry point.'''
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
    ).add_file(
        "utils.py", 
        """
def helper_function(x):
    '''Helper function.'''
    return x * 2

class UtilityClass:
    def __init__(self):
        self.value = 0
    
    def increment(self):
        self.value += 1
"""
    ).add_file(
        "README.md",
        """
# Sample Project

This is a sample Python project for testing.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
python main.py
```
"""
    ).add_file(
        "requirements.txt",
        """
requests>=2.25.0
fastapi>=0.95.0
"""
    ).add_file(
        "config.json",
        """
{
    "app_name": "Sample App",
    "debug": true,
    "version": "1.0.0"
}
"""
    )


def create_sample_fastapi_repo():
    """Create a sample FastAPI repository for testing."""
    return MockRepositoryBuilder().add_file(
        "app.py",
        """
from fastapi import FastAPI

app = FastAPI(title="Sample API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
"""
    ).add_file(
        "models.py",
        """
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

class User(BaseModel):
    username: str
    email: str
    full_name: str = None
"""
    ).add_file(
        "database.py",
        """
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
"""
    )


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_request = None
    
    def generate_content(self, prompt: str):
        """Mock content generation."""
        self.call_count += 1
        self.last_request = prompt
        
        mock_response = Mock()
        mock_response.text = self.responses.get(prompt, "Mock response")
        mock_response.parts = [Mock(text=mock_response.text)]
        
        return mock_response
    
    def call(self, api_kwargs, model_type=None):
        """Mock API call."""
        self.call_count += 1
        self.last_request = api_kwargs
        
        # Return different responses based on model type or content
        if "embedding" in str(model_type).lower():
            return Mock(data=[Mock(embedding=[0.1, 0.2, 0.3, 0.4])])
        else:
            return Mock(
                choices=[Mock(message=Mock(content="Mock LLM response"))],
                usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)
            )
    
    async def acall(self, api_kwargs, model_type=None):
        """Mock async API call."""
        return self.call(api_kwargs, model_type)


class MockWikiGenerator:
    """Mock wiki generator for testing."""
    
    def __init__(self):
        self.generate_count = 0
        
    def generate_wiki_structure(self, repo_path: str, repo_url: str, language: str = "en"):
        """Mock wiki structure generation."""
        self.generate_count += 1
        
        return {
            "id": "test_wiki",
            "title": "Test Wiki Documentation",
            "description": f"Auto-generated documentation for {repo_url}",
            "pages": [
                {
                    "id": "overview",
                    "title": "Project Overview",
                    "content": "# Project Overview\n\nThis is a test project.",
                    "filePaths": ["README.md"],
                    "importance": "high",
                    "relatedPages": ["architecture"]
                },
                {
                    "id": "architecture", 
                    "title": "Architecture",
                    "content": "# Architecture\n\nSystem architecture details.",
                    "filePaths": ["main.py"],
                    "importance": "high", 
                    "relatedPages": ["overview"]
                }
            ],
            "sections": [
                {
                    "id": "core",
                    "title": "Core Documentation",
                    "pages": ["overview", "architecture"],
                    "subsections": []
                }
            ],
            "rootSections": ["core"]
        }
    
    def _generate_architecture_diagram(self, repo_structure):
        """Mock architecture diagram generation."""
        return """
graph TD
    A[Main Module] --> B[Utils]
    A --> C[Config]
    B --> D[Database]
"""
    
    def _generate_data_flow_diagram(self, repo_structure):
        """Mock data flow diagram generation."""
        return """
flowchart LR
    Input --> Process
    Process --> Output
"""


class AsyncMockContext:
    """Async context manager for testing."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def assert_valid_wiki_structure(wiki_structure: Dict[Any, Any]):
    """Assert that wiki structure is valid."""
    assert "title" in wiki_structure
    assert "pages" in wiki_structure
    assert isinstance(wiki_structure["pages"], list)
    
    for page in wiki_structure["pages"]:
        assert "id" in page
        assert "title" in page
        assert "content" in page
        assert "filePaths" in page
        assert "importance" in page
        assert "relatedPages" in page


def assert_valid_mermaid_diagram(diagram: str):
    """Assert that Mermaid diagram syntax is valid."""
    diagram = diagram.strip()
    
    # Basic validation - should contain Mermaid keywords
    mermaid_keywords = ["graph", "flowchart", "sequenceDiagram", "classDiagram", "gitgraph"]
    assert any(keyword in diagram for keyword in mermaid_keywords)
    
    # Should not be empty
    assert len(diagram) > 0
    
    # Should have proper structure (at least one arrow or connection)
    assert "-->" in diagram or "->" in diagram or ":" in diagram


def create_mock_file_system(files: Dict[str, str]):
    """Create mock file system for testing."""
    import os
    from unittest.mock import patch, mock_open
    
    def mock_exists(path):
        return any(path.endswith(filename) for filename in files.keys())
    
    def mock_isfile(path):
        return any(path.endswith(filename) for filename in files.keys())
    
    def mock_listdir(path):
        return list(files.keys())
    
    def mock_open_file(path, mode='r', **kwargs):
        for filename, content in files.items():
            if path.endswith(filename):
                return mock_open(read_data=content).return_value
        raise FileNotFoundError(f"No such file: {path}")
    
    return {
        'exists': patch('os.path.exists', side_effect=mock_exists),
        'isfile': patch('os.path.isfile', side_effect=mock_isfile),
        'listdir': patch('os.listdir', side_effect=mock_listdir),
        'open': patch('builtins.open', side_effect=mock_open_file)
    }