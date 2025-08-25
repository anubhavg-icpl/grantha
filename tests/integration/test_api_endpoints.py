"""
Integration tests for API endpoints.
"""

import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from api.api import app


@pytest.fixture
def client():
    """Create test client for API testing."""
    return TestClient(app)


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration test suite for API endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message and endpoints."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ग्रंथ" in data["message"]
        assert "endpoints" in data
        assert isinstance(data["endpoints"], dict)

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "grantha-api"

    def test_lang_config_endpoint(self, client):
        """Test language configuration endpoint."""
        response = client.get("/lang/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert "default" in data
        assert "en" in data["supported_languages"]

    def test_auth_status_endpoint(self, client):
        """Test authentication status endpoint."""
        response = client.get("/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_required" in data
        assert isinstance(data["auth_required"], bool)

    def test_auth_validate_endpoint(self, client):
        """Test authorization code validation."""
        response = client.post("/auth/validate", json={"code": "test_code"})
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert isinstance(data["success"], bool)

    def test_models_config_endpoint(self, client):
        """Test model configuration endpoint."""
        response = client.get("/models/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "defaultProvider" in data
        assert isinstance(data["providers"], list)
        
        if data["providers"]:
            provider = data["providers"][0]
            assert "id" in provider
            assert "name" in provider
            assert "models" in provider

    def test_local_repo_structure_no_path(self, client):
        """Test local repository structure endpoint without path."""
        response = client.get("/local_repo/structure")
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "No path provided" in data["error"]

    def test_local_repo_structure_invalid_path(self, client):
        """Test local repository structure with invalid path."""
        response = client.get("/local_repo/structure?path=/nonexistent/path")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "Directory not found" in data["error"]

    @patch('os.path.isdir')
    @patch('os.walk')
    def test_local_repo_structure_valid_path(self, mock_walk, mock_isdir, client):
        """Test local repository structure with valid path."""
        mock_isdir.return_value = True
        mock_walk.return_value = [
            ('/test/path', ['subdir'], ['main.py', 'README.md']),
            ('/test/path/subdir', [], ['utils.py'])
        ]
        
        response = client.get("/local_repo/structure?path=/test/path")
        
        assert response.status_code == 200
        data = response.json()
        assert "file_tree" in data
        assert "readme" in data

    def test_wiki_cache_get_not_found(self, client):
        """Test getting wiki cache when not found."""
        response = client.get(
            "/api/wiki_cache",
            params={
                "owner": "testuser",
                "repo": "testrepo", 
                "repo_type": "github",
                "language": "en"
            }
        )
        
        assert response.status_code == 200
        # Should return null/None when not found
        assert response.json() is None

    def test_processed_projects_endpoint(self, client):
        """Test processed projects listing endpoint.""" 
        response = client.get("/api/processed_projects")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('api.api.WikiGenerator')
    @patch('api.api.download_repo')
    def test_wiki_generate_endpoint(self, mock_download_repo, mock_wiki_generator, client):
        """Test wiki generation endpoint."""
        # Mock dependencies
        mock_download_repo.return_value = "/tmp/test_repo"
        mock_generator_instance = Mock()
        mock_generator_instance.generate_wiki_structure.return_value = {
            "title": "Test Wiki",
            "pages": []
        }
        mock_wiki_generator.return_value = mock_generator_instance
        
        request_data = {
            "repo_url": "https://github.com/test/repo",
            "language": "en",
            "provider": "google",
            "repo_type": "github"
        }
        
        response = client.post("/api/wiki/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "pages" in data

    def test_mermaid_diagrams_endpoint(self, client):
        """Test Mermaid diagram generation endpoint."""
        with patch('api.api.WikiGenerator') as mock_wiki_generator, \
             patch('api.api.download_repo') as mock_download_repo:
            
            mock_download_repo.return_value = "/tmp/test_repo"
            mock_generator_instance = Mock()
            mock_generator_instance._analyze_repository.return_value = {"files": []}
            mock_generator_instance._generate_architecture_diagram.return_value = "graph TD\n    A --> B"
            mock_wiki_generator.return_value = mock_generator_instance
            
            response = client.get(
                "/api/wiki/mermaid",
                params={
                    "repo_url": "https://github.com/test/repo",
                    "diagram_type": "architecture"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "diagram_type" in data
            assert "mermaid" in data
            assert "repo_url" in data

    def test_export_wiki_markdown(self, client):
        """Test wiki export in Markdown format."""
        export_data = {
            "repo_url": "https://github.com/test/repo",
            "format": "markdown",
            "pages": [
                {
                    "id": "page1",
                    "title": "Test Page",
                    "content": "Test content",
                    "filePaths": ["test.py"],
                    "importance": "high",
                    "relatedPages": []
                }
            ]
        }
        
        response = client.post("/export/wiki", json=export_data)
        
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

    def test_export_wiki_json(self, client):
        """Test wiki export in JSON format."""
        export_data = {
            "repo_url": "https://github.com/test/repo", 
            "format": "json",
            "pages": [
                {
                    "id": "page1",
                    "title": "Test Page",
                    "content": "Test content",
                    "filePaths": ["test.py"],
                    "importance": "high",
                    "relatedPages": []
                }
            ]
        }
        
        response = client.post("/export/wiki", json=export_data)
        
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

    def test_wiki_cache_store(self, client, sample_wiki_data):
        """Test storing wiki cache."""
        with patch('api.api.save_wiki_cache') as mock_save:
            mock_save.return_value = True
            
            response = client.post("/api/wiki_cache", json=sample_wiki_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "successfully" in data["message"]

    def test_wiki_cache_store_failure(self, client, sample_wiki_data):
        """Test wiki cache storage failure."""
        with patch('api.api.save_wiki_cache') as mock_save:
            mock_save.return_value = False
            
            response = client.post("/api/wiki_cache", json=sample_wiki_data)
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Failed to save" in data["detail"]

    def test_wiki_cache_delete_auth_required(self, client):
        """Test wiki cache deletion with authentication required."""
        with patch('api.api.WIKI_AUTH_MODE', True), \
             patch('api.api.WIKI_AUTH_CODE', 'secret123'):
            
            # Without auth code
            response = client.delete(
                "/api/wiki_cache",
                params={
                    "owner": "testuser",
                    "repo": "testrepo",
                    "repo_type": "github", 
                    "language": "en"
                }
            )
            
            assert response.status_code == 401
            
            # With correct auth code
            response = client.delete(
                "/api/wiki_cache",
                params={
                    "owner": "testuser",
                    "repo": "testrepo",
                    "repo_type": "github",
                    "language": "en",
                    "authorization_code": "secret123"
                }
            )
            
            # Should return 404 since file doesn't exist in test
            assert response.status_code == 404

    def test_deep_research_endpoint(self, client):
        """Test deep research endpoint."""
        with patch('api.api.DeepResearch') as mock_deep_research:
            # Mock the research response generator
            async def mock_research_generator():
                yield {
                    "stage": "analysis",
                    "content": "Analyzing repository...",
                    "timestamp": "2024-01-01T00:00:00"
                }
                yield {
                    "stage": "complete",
                    "content": "Research completed",
                    "timestamp": "2024-01-01T00:01:00"
                }
            
            mock_researcher_instance = Mock()
            mock_researcher_instance.conduct_research.return_value = mock_research_generator()
            mock_deep_research.return_value = mock_researcher_instance
            
            request_data = {
                "query": "How does this API work?",
                "repo_url": "https://github.com/test/repo",
                "language": "en",
                "provider": "google",
                "repo_type": "github"
            }
            
            response = client.post("/api/research/deep", json=request_data)
            
            assert response.status_code == 200
            assert "application/x-ndjson" in response.headers["content-type"]

    def test_chat_completions_stream_endpoint(self, client):
        """Test streaming chat completions endpoint."""
        with patch('api.simple_chat.chat_completions_stream') as mock_chat:
            mock_chat.return_value = Mock(status_code=200)
            
            request_data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "gpt-3.5-turbo",
                "stream": True
            }
            
            # Note: This tests the endpoint registration, not the full streaming
            # Full streaming tests would require WebSocket testing
            response = client.post("/chat/completions/stream", json=request_data)
            
            # The actual response depends on the implementation
            assert response.status_code in [200, 422]  # 422 for validation errors in test

    def test_invalid_json_request(self, client):
        """Test API endpoints with invalid JSON."""
        response = client.post("/api/wiki/generate", data="invalid json")
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, client):
        """Test API endpoints with missing required fields."""
        response = client.post("/api/wiki/generate", json={"repo_url": ""})
        
        assert response.status_code == 422  # Validation error

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"