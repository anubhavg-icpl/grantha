"""
Unit tests for OpenAI client implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Generator

from api.openai_client import OpenAIClient
from adalflow.core.types import ModelType


@pytest.fixture
def openai_client():
    """Create OpenAI client instance for testing."""
    return OpenAIClient()


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(content="Test response"),
            finish_reason="stop"
        )
    ]
    mock_response.usage = Mock(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15
    )
    return mock_response


@pytest.fixture
def mock_openai_streaming_response():
    """Mock OpenAI streaming API response."""
    mock_chunks = [
        Mock(
            choices=[Mock(delta=Mock(content="Hello"))],
            finish_reason=None
        ),
        Mock(
            choices=[Mock(delta=Mock(content=" world"))],
            finish_reason=None  
        ),
        Mock(
            choices=[Mock(delta=Mock(content="!"))],
            finish_reason="stop"
        )
    ]
    return iter(mock_chunks)


@pytest.mark.unit
class TestOpenAIClient:
    """Test suite for OpenAI client."""
    
    def test_client_initialization(self, openai_client):
        """Test OpenAI client initialization."""
        assert openai_client is not None
        assert hasattr(openai_client, 'sync_client')
        assert hasattr(openai_client, 'async_client')

    def test_get_model_types(self, openai_client):
        """Test getting supported model types."""
        model_types = openai_client.get_supported_model_types()
        assert ModelType.LLM in model_types
        assert ModelType.EMBEDDER in model_types
        
    @patch('api.openai_client.OpenAI')
    def test_call_with_mock_response(self, mock_openai, openai_client, mock_openai_response):
        """Test basic call functionality with mocked response."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client
        
        # Reinitialize client with mocked OpenAI
        client = OpenAIClient()
        
        api_kwargs = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        with patch.object(client, 'sync_client', mock_client):
            response = client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
        
        assert response is not None
        mock_client.chat.completions.create.assert_called_once()

    @patch('api.openai_client.OpenAI')  
    def test_call_with_streaming(self, mock_openai, openai_client, mock_openai_streaming_response):
        """Test streaming call functionality."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_streaming_response
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        api_kwargs = {
            "model": "gpt-3.5-turbo", 
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
        
        with patch.object(client, 'sync_client', mock_client):
            response = client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)
        
        # For streaming, response should be a generator
        assert hasattr(response, '__iter__')

    @patch('api.openai_client.OpenAI')
    def test_embeddings_call(self, mock_openai, openai_client):
        """Test embeddings API call."""
        mock_client = Mock()
        mock_embedding_response = Mock()
        mock_embedding_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3, 0.4])
        ]
        mock_client.embeddings.create.return_value = mock_embedding_response
        mock_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        api_kwargs = {
            "model": "text-embedding-ada-002",
            "input": "Test text for embedding"
        }
        
        with patch.object(client, 'sync_client', mock_client):
            response = client.call(api_kwargs=api_kwargs, model_type=ModelType.EMBEDDER)
        
        assert response is not None
        mock_client.embeddings.create.assert_called_once()

    def test_convert_inputs_to_api_kwargs(self, openai_client):
        """Test input conversion to API kwargs."""
        # This would test the internal conversion logic
        # Implementation depends on the specific method signature
        pass

    def test_error_handling(self, openai_client):
        """Test error handling for API failures."""
        from openai import RateLimitError, APITimeoutError
        
        with patch.object(openai_client, 'sync_client') as mock_client:
            mock_client.chat.completions.create.side_effect = RateLimitError(
                message="Rate limit exceeded",
                response=Mock(status_code=429),
                body={}
            )
            
            api_kwargs = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            
            with pytest.raises(RateLimitError):
                openai_client.call(api_kwargs=api_kwargs, model_type=ModelType.LLM)

    @pytest.mark.asyncio
    @patch('api.openai_client.AsyncOpenAI')
    async def test_async_call(self, mock_async_openai, openai_client, mock_openai_response):
        """Test asynchronous API calls."""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_async_openai.return_value = mock_client
        
        client = OpenAIClient()
        
        api_kwargs = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        with patch.object(client, 'async_client', mock_client):
            response = await client.acall(api_kwargs=api_kwargs, model_type=ModelType.LLM)
        
        assert response is not None