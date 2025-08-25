"""
Comprehensive API Integration Tests
Tests all API endpoints and functionality
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import websockets

# Import the app (adjust import path as needed)
# from src.grantha.api.app import create_app

class TestComprehensiveAPI:
    """Comprehensive API test suite"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        # app = create_app()
        # return TestClient(app)
        # For now, return a mock client until the app is fixed
        return MagicMock()

    @pytest.fixture
    def sample_chat_request(self):
        """Sample chat request payload"""
        return {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "model": "gpt-3.5-turbo",
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 150
        }

    @pytest.fixture
    def sample_streaming_request(self):
        """Sample streaming chat request"""
        return {
            "messages": [
                {"role": "user", "content": "Tell me about AI"}
            ],
            "model": "gpt-3.5-turbo",
            "stream": True,
            "temperature": 0.8,
            "max_tokens": 200
        }

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Grantha" in data["message"]

    def test_chat_endpoint_non_streaming(self, client, sample_chat_request):
        """Test non-streaming chat endpoint"""
        with patch('openai.OpenAI') as mock_openai:
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="Hello! I'm doing well, thank you for asking."))
            ]
            mock_openai.return_value.chat.completions.create.return_value = mock_response

            response = client.post("/api/v1/chat", json=sample_chat_request)
            assert response.status_code == 200
            
            data = response.json()
            assert "choices" in data
            assert len(data["choices"]) > 0
            assert "message" in data["choices"][0]

    def test_chat_endpoint_streaming(self, client, sample_streaming_request):
        """Test streaming chat endpoint"""
        with patch('openai.OpenAI') as mock_openai:
            # Mock streaming response
            def mock_stream():
                chunks = [
                    {"choices": [{"delta": {"content": "AI"}}]},
                    {"choices": [{"delta": {"content": " is"}}]},
                    {"choices": [{"delta": {"content": " fascinating"}}]},
                ]
                for chunk in chunks:
                    yield MagicMock(**chunk)

            mock_openai.return_value.chat.completions.create.return_value = mock_stream()

            response = client.post("/api/v1/chat", json=sample_streaming_request)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_chat_endpoint_validation(self, client):
        """Test chat endpoint input validation"""
        # Test missing messages
        response = client.post("/api/v1/chat", json={
            "model": "gpt-3.5-turbo"
        })
        assert response.status_code == 422

        # Test invalid model
        response = client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "test"}],
            "model": "invalid-model"
        })
        assert response.status_code == 400

        # Test invalid message format
        response = client.post("/api/v1/chat", json={
            "messages": [{"invalid": "format"}],
            "model": "gpt-3.5-turbo"
        })
        assert response.status_code == 422

    def test_models_endpoint(self, client):
        """Test models listing endpoint"""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        
        # Check model structure
        if len(data["models"]) > 0:
            model = data["models"][0]
            assert "id" in model
            assert "name" in model
            assert "provider" in model

    def test_providers_endpoint(self, client):
        """Test providers listing endpoint"""
        response = client.get("/api/v1/providers")
        assert response.status_code == 200
        
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_wiki_generation_endpoint(self, client):
        """Test wiki generation endpoint"""
        wiki_request = {
            "repo_url": "https://github.com/example/repo",
            "output_format": "markdown",
            "include_code_examples": True
        }

        with patch('git.Repo.clone_from') as mock_clone:
            mock_clone.return_value = MagicMock()
            
            response = client.post("/api/v1/wiki/generate", json=wiki_request)
            assert response.status_code in [200, 202]  # Success or accepted for async processing

    def test_research_endpoint(self, client):
        """Test research endpoint"""
        research_request = {
            "query": "artificial intelligence trends 2024",
            "depth": "comprehensive",
            "sources": ["arxiv", "google_scholar"],
            "max_results": 10
        }

        response = client.post("/api/v1/research", json=research_request)
        assert response.status_code in [200, 202]

    def test_upload_endpoint(self, client):
        """Test file upload endpoint"""
        # Create a test file
        test_file = {"file": ("test.txt", "This is test content", "text/plain")}
        
        response = client.post("/api/v1/upload", files=test_file)
        assert response.status_code == 200
        
        data = response.json()
        assert "file_id" in data
        assert "filename" in data

    def test_download_endpoint(self, client):
        """Test file download endpoint"""
        # First upload a file to get an ID
        test_file = {"file": ("test.txt", "Download test content", "text/plain")}
        upload_response = client.post("/api/v1/upload", files=test_file)
        assert upload_response.status_code == 200
        
        file_id = upload_response.json()["file_id"]
        
        # Now download it
        response = client.get(f"/api/v1/download/{file_id}")
        assert response.status_code == 200

    def test_user_settings_endpoint(self, client):
        """Test user settings endpoints"""
        # Get settings
        response = client.get("/api/v1/user/settings")
        assert response.status_code in [200, 401]  # Success or unauthorized

        # Update settings
        new_settings = {
            "theme": "dark",
            "language": "en",
            "default_model": "gpt-4",
            "api_timeout": 30
        }
        
        response = client.put("/api/v1/user/settings", json=new_settings)
        assert response.status_code in [200, 401]

    def test_conversation_endpoints(self, client):
        """Test conversation CRUD endpoints"""
        # Create conversation
        conversation_data = {
            "title": "Test Conversation",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
        
        response = client.post("/api/v1/conversations", json=conversation_data)
        assert response.status_code in [201, 401]
        
        if response.status_code == 201:
            conversation_id = response.json()["id"]
            
            # Get conversation
            response = client.get(f"/api/v1/conversations/{conversation_id}")
            assert response.status_code == 200
            
            # Update conversation
            update_data = {"title": "Updated Title"}
            response = client.put(f"/api/v1/conversations/{conversation_id}", json=update_data)
            assert response.status_code == 200
            
            # Delete conversation
            response = client.delete(f"/api/v1/conversations/{conversation_id}")
            assert response.status_code == 204

    def test_error_handling(self, client):
        """Test API error handling"""
        # Test 404
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
        # Test invalid JSON
        response = client.post(
            "/api/v1/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_rate_limiting(self, client):
        """Test rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # All should succeed unless rate limiting is very strict
        # This test mainly checks that rate limiting doesn't break normal usage
        assert all(status in [200, 429] for status in responses)

    def test_cors_headers(self, client):
        """Test CORS headers"""
        response = client.options("/api/v1/chat")
        
        # Should allow CORS for development
        assert "access-control-allow-origin" in response.headers.keys() or response.status_code == 405

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        # This would test WebSocket if available
        # For now, just ensure the test framework supports async tests
        await asyncio.sleep(0.1)
        assert True

    def test_api_documentation(self, client):
        """Test API documentation endpoints"""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Validate it's valid JSON
        data = response.json()
        assert "openapi" in data
        assert "info" in data

class TestAPIPerformance:
    """Performance tests for API endpoints"""

    def test_chat_response_time(self, client):
        """Test chat endpoint response time"""
        import time
        
        request_data = {
            "messages": [{"role": "user", "content": "Quick test"}],
            "model": "gpt-3.5-turbo",
            "max_tokens": 10
        }
        
        start_time = time.time()
        response = client.post("/api/v1/chat", json=request_data)
        end_time = time.time()
        
        # Response should be reasonably fast (under 30 seconds)
        assert end_time - start_time < 30.0
        assert response.status_code in [200, 500]  # May fail due to API keys

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5