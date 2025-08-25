"""
End-to-end tests for complete wiki generation workflow.
"""

import pytest
import tempfile
import shutil
import json
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from api.api import app


@pytest.fixture
def e2e_client():
    """Create test client for E2E testing."""
    return TestClient(app)


@pytest.fixture
def mock_repository():
    """Create a mock repository structure for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample files
    files = {
        "main.py": """
def main():
    '''Main application entry point.'''
    print("Hello, Grantha!")
    return 0

if __name__ == "__main__":
    main()
""",
        "api.py": """
from fastapi import FastAPI

app = FastAPI(title="Test API")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
""",
        "utils.py": """
def helper_function(data):
    '''Utility function for data processing.'''
    return data.upper()

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        return helper_function(item)
""",
        "README.md": """
# Test Repository

This is a test repository for Grantha wiki generation.

## Features
- FastAPI web application
- Data processing utilities
- Comprehensive documentation

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from main import main
main()
```
""",
        "requirements.txt": """
fastapi>=0.95.0
uvicorn>=0.21.1
pydantic>=2.0.0
pytest>=7.0.0
""",
        "config.json": """
{
    "app_name": "Test Application",
    "debug": true,
    "database_url": "sqlite:///test.db"
}
"""
    }
    
    for filename, content in files.items():
        with open(os.path.join(temp_dir, filename), 'w') as f:
            f.write(content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.mark.e2e
@pytest.mark.slow
class TestWikiGenerationWorkflow:
    """End-to-end test suite for wiki generation workflow."""
    
    def test_complete_wiki_generation_flow(self, e2e_client, mock_repository):
        """Test complete wiki generation from repository to export."""
        repo_url = "https://github.com/test/example-repo"
        
        with patch('api.api.download_repo') as mock_download, \
             patch('api.api.WikiGenerator') as mock_wiki_gen:
            
            # Mock repository download
            mock_download.return_value = mock_repository
            
            # Mock wiki generator
            mock_generator = Mock()
            mock_wiki_structure = {
                "id": "example_repo_wiki",
                "title": "Example Repository Wiki",
                "description": "Auto-generated documentation for example repository",
                "pages": [
                    {
                        "id": "overview",
                        "title": "Project Overview", 
                        "content": "# Project Overview\n\nThis repository contains a FastAPI application with utilities.",
                        "filePaths": ["README.md"],
                        "importance": "high",
                        "relatedPages": ["api_reference", "utilities"]
                    },
                    {
                        "id": "api_reference",
                        "title": "API Reference",
                        "content": "# API Reference\n\n## Endpoints\n\n### GET /\nReturns welcome message.",
                        "filePaths": ["api.py"],
                        "importance": "high", 
                        "relatedPages": ["overview"]
                    },
                    {
                        "id": "utilities",
                        "title": "Utility Functions",
                        "content": "# Utility Functions\n\n## DataProcessor\nClass for processing data.",
                        "filePaths": ["utils.py"],
                        "importance": "medium",
                        "relatedPages": ["overview"]
                    }
                ],
                "sections": [
                    {
                        "id": "core",
                        "title": "Core Components",
                        "pages": ["overview", "api_reference"],
                        "subsections": []
                    },
                    {
                        "id": "helpers", 
                        "title": "Helper Modules",
                        "pages": ["utilities"],
                        "subsections": []
                    }
                ],
                "rootSections": ["core", "helpers"]
            }
            
            mock_generator.generate_wiki_structure.return_value = mock_wiki_structure
            mock_wiki_gen.return_value = mock_generator
            
            # Step 1: Generate wiki structure
            generation_request = {
                "repo_url": repo_url,
                "language": "en",
                "provider": "google",
                "model": "gemini-2.5-flash",
                "repo_type": "github"
            }
            
            response = e2e_client.post("/api/wiki/generate", json=generation_request)
            assert response.status_code == 200
            
            wiki_data = response.json()
            assert "title" in wiki_data
            assert "pages" in wiki_data
            assert len(wiki_data["pages"]) > 0
            
            # Step 2: Store generated wiki in cache
            cache_data = {
                "repo": {
                    "owner": "test",
                    "repo": "example-repo",
                    "type": "github",
                    "repoUrl": repo_url
                },
                "language": "en",
                "wiki_structure": wiki_data,
                "generated_pages": {page["id"]: page for page in wiki_data["pages"]},
                "provider": "google",
                "model": "gemini-2.5-flash"
            }
            
            with patch('api.api.save_wiki_cache') as mock_save:
                mock_save.return_value = True
                
                response = e2e_client.post("/api/wiki_cache", json=cache_data)
                assert response.status_code == 200
                assert "successfully" in response.json()["message"]
            
            # Step 3: Retrieve cached wiki
            with patch('api.api.read_wiki_cache') as mock_read:
                mock_read.return_value = Mock(**cache_data)
                
                response = e2e_client.get(
                    "/api/wiki_cache",
                    params={
                        "owner": "test",
                        "repo": "example-repo", 
                        "repo_type": "github",
                        "language": "en"
                    }
                )
                assert response.status_code == 200
                cached_data = response.json()
                assert cached_data is not None
            
            # Step 4: Export wiki as Markdown
            export_request = {
                "repo_url": repo_url,
                "format": "markdown",
                "pages": wiki_data["pages"]
            }
            
            response = e2e_client.post("/export/wiki", json=export_request)
            assert response.status_code == 200
            assert "text/markdown" in response.headers["content-type"]
            assert "attachment" in response.headers["content-disposition"]
            
            # Verify exported content contains expected elements
            content = response.content.decode('utf-8')
            assert "# Wiki Documentation for" in content
            assert "Table of Contents" in content
            assert "Project Overview" in content
            
            # Step 5: Export wiki as JSON
            export_request["format"] = "json"
            
            response = e2e_client.post("/export/wiki", json=export_request)
            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]
            
            # Verify JSON structure
            json_content = json.loads(response.content.decode('utf-8'))
            assert "metadata" in json_content
            assert "pages" in json_content
            assert len(json_content["pages"]) > 0

    def test_mermaid_diagram_generation_flow(self, e2e_client, mock_repository):
        """Test Mermaid diagram generation workflow."""
        repo_url = "https://github.com/test/example-repo"
        
        with patch('api.api.download_repo') as mock_download, \
             patch('api.api.WikiGenerator') as mock_wiki_gen:
            
            mock_download.return_value = mock_repository
            
            # Mock wiki generator and diagram generation
            mock_generator = Mock()
            mock_repo_structure = {
                "files": ["main.py", "api.py", "utils.py"],
                "structure": {
                    "python_files": ["main.py", "api.py", "utils.py"],
                    "web_framework": ["api.py"]
                }
            }
            mock_generator._analyze_repository.return_value = mock_repo_structure
            
            # Mock different diagram types
            mock_generator._generate_architecture_diagram.return_value = """
graph TD
    A[main.py] --> B[api.py]
    A --> C[utils.py]
    B --> D[FastAPI App]
    C --> E[Data Processing]
"""
            
            mock_generator._generate_data_flow_diagram.return_value = """
flowchart LR
    Input --> Process[Data Processing]
    Process --> Output
    Process --> Store[Database]
"""
            
            mock_generator._generate_api_flow_diagram.return_value = """
sequenceDiagram
    Client->>+API: GET /
    API-->>-Client: Hello World
    Client->>+API: GET /health
    API-->>-Client: Status
"""
            
            mock_wiki_gen.return_value = mock_generator
            
            # Test architecture diagram
            response = e2e_client.get(
                "/api/wiki/mermaid",
                params={
                    "repo_url": repo_url,
                    "diagram_type": "architecture"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["diagram_type"] == "architecture"
            assert "graph TD" in data["mermaid"]
            
            # Test data flow diagram
            response = e2e_client.get(
                "/api/wiki/mermaid",
                params={
                    "repo_url": repo_url,
                    "diagram_type": "data-flow"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["diagram_type"] == "data-flow"
            assert "flowchart" in data["mermaid"]
            
            # Test API flow diagram
            response = e2e_client.get(
                "/api/wiki/mermaid", 
                params={
                    "repo_url": repo_url,
                    "diagram_type": "api-flow"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["diagram_type"] == "api-flow"
            assert "sequenceDiagram" in data["mermaid"]

    def test_deep_research_workflow(self, e2e_client, mock_repository):
        """Test deep research workflow."""
        with patch('api.api.DeepResearch') as mock_deep_research:
            
            # Mock research stages
            async def mock_research_stages():
                stages = [
                    {
                        "stage": "initialization",
                        "content": "Starting deep research analysis...",
                        "timestamp": "2024-01-01T00:00:00"
                    },
                    {
                        "stage": "repository_analysis",
                        "content": "Analyzing repository structure and dependencies...",
                        "timestamp": "2024-01-01T00:00:30"
                    },
                    {
                        "stage": "code_analysis", 
                        "content": "Examining code patterns and architecture...",
                        "timestamp": "2024-01-01T00:01:00"
                    },
                    {
                        "stage": "documentation_review",
                        "content": "Reviewing existing documentation and comments...",
                        "timestamp": "2024-01-01T00:01:30"
                    },
                    {
                        "stage": "synthesis",
                        "content": "Synthesizing findings into comprehensive analysis...",
                        "timestamp": "2024-01-01T00:02:00"
                    },
                    {
                        "stage": "complete",
                        "content": "Deep research completed. The repository implements a FastAPI web application with modular architecture.",
                        "timestamp": "2024-01-01T00:02:30",
                        "findings": {
                            "architecture": "FastAPI-based web application",
                            "key_components": ["API endpoints", "Data processing utilities", "Configuration management"],
                            "recommendations": ["Add API versioning", "Implement authentication", "Add comprehensive logging"]
                        }
                    }
                ]
                
                for stage in stages:
                    yield stage
            
            mock_researcher = Mock()
            mock_researcher.conduct_research.return_value = mock_research_stages()
            mock_deep_research.return_value = mock_researcher
            
            # Test deep research request
            research_request = {
                "query": "How is this FastAPI application structured and what are the main components?",
                "repo_url": "https://github.com/test/example-repo",
                "language": "en",
                "provider": "google",
                "repo_type": "github"
            }
            
            response = e2e_client.post("/api/research/deep", json=research_request)
            assert response.status_code == 200
            assert "application/x-ndjson" in response.headers["content-type"]
            
            # Verify streaming response format
            content = response.content.decode('utf-8')
            lines = [line for line in content.split('\n') if line.strip()]
            assert len(lines) > 0
            
            # Each line should be valid JSON
            for line in lines:
                data = json.loads(line)
                assert "stage" in data
                assert "content" in data
                assert "timestamp" in data

    def test_error_handling_workflow(self, e2e_client):
        """Test error handling throughout the workflow."""
        # Test with invalid repository URL
        invalid_request = {
            "repo_url": "invalid-url",
            "language": "en",
            "provider": "google",
            "repo_type": "github"
        }
        
        with patch('api.api.download_repo') as mock_download:
            mock_download.side_effect = Exception("Repository not found")
            
            response = e2e_client.post("/api/wiki/generate", json=invalid_request)
            assert response.status_code == 500
            assert "Failed to generate wiki structure" in response.json()["detail"]
        
        # Test with invalid provider
        invalid_provider_request = {
            "repo_url": "https://github.com/test/repo",
            "language": "en", 
            "provider": "invalid_provider",
            "repo_type": "github"
        }
        
        response = e2e_client.post("/api/wiki/generate", json=invalid_provider_request)
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [422, 500]
        
        # Test with unsupported language
        unsupported_lang_request = {
            "repo_url": "https://github.com/test/repo",
            "language": "unsupported_lang",
            "provider": "google",
            "repo_type": "github"
        }
        
        response = e2e_client.post("/api/wiki/generate", json=unsupported_lang_request)
        # Should fallback to default language or handle appropriately
        assert response.status_code in [200, 422]

    @pytest.mark.network
    def test_local_repository_workflow(self, e2e_client, mock_repository):
        """Test workflow with local repository."""
        # Test local repository structure endpoint
        response = e2e_client.get(f"/local_repo/structure?path={mock_repository}")
        assert response.status_code == 200
        
        data = response.json()
        assert "file_tree" in data
        assert "readme" in data
        
        # Verify expected files are detected
        file_tree = data["file_tree"]
        assert "main.py" in file_tree
        assert "api.py" in file_tree
        assert "utils.py" in file_tree
        
        # Verify README content is captured
        readme_content = data["readme"]
        assert "Test Repository" in readme_content or readme_content == ""

    def test_configuration_endpoints_workflow(self, e2e_client):
        """Test configuration-related endpoints workflow."""
        # Test model configuration
        response = e2e_client.get("/models/config")
        assert response.status_code == 200
        
        config = response.json()
        assert "providers" in config
        assert "defaultProvider" in config
        
        # Test language configuration
        response = e2e_client.get("/lang/config")
        assert response.status_code == 200
        
        lang_config = response.json()
        assert "supported_languages" in lang_config
        assert "default" in lang_config
        assert "en" in lang_config["supported_languages"]
        
        # Test authentication status
        response = e2e_client.get("/auth/status")
        assert response.status_code == 200
        
        auth_status = response.json()
        assert "auth_required" in auth_status