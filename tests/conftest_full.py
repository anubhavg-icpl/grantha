"""
pytest configuration and fixtures for Grantha test suite.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Set test environment variables before importing modules
os.environ["TESTING"] = "1"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["OPENROUTER_API_KEY"] = "test_openrouter_key"

from api.api import app
from api.config import configs


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Mock environment variables for testing."""
    env_vars = {
        "GOOGLE_API_KEY": "test_google_api_key",
        "OPENAI_API_KEY": "test_openai_api_key",
        "OPENROUTER_API_KEY": "test_openrouter_api_key",
        "AWS_ACCESS_KEY_ID": "test_aws_access_key",
        "AWS_SECRET_ACCESS_KEY": "test_aws_secret_key",
        "AWS_REGION": "us-east-1",
        "GRANTHA_AUTH_MODE": "False",
        "GRANTHA_AUTH_CODE": "",
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def temp_repo_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing repository operations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_google_genai():
    """Mock Google Generative AI for testing."""
    with patch('google.generativeai.configure') as mock_configure, \
         patch('google.generativeai.GenerativeModel') as mock_model:
        
        mock_response = Mock()
        mock_response.text = "Test response from Gemini"
        mock_response.parts = [Mock(text="Test response from Gemini")]
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        yield {
            'configure': mock_configure,
            'model': mock_model,
            'response': mock_response
        }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('openai.OpenAI') as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response from OpenAI"))]
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_client.return_value = mock_client_instance
        
        yield mock_client


@pytest.fixture
def sample_wiki_data():
    """Sample wiki data for testing."""
    return {
        "wiki_structure": {
            "id": "test_wiki",
            "title": "Test Wiki",
            "description": "A test wiki for unit testing",
            "pages": [
                {
                    "id": "page1",
                    "title": "Page 1",
                    "content": "Content of page 1",
                    "filePaths": ["file1.py"],
                    "importance": "high",
                    "relatedPages": ["page2"]
                },
                {
                    "id": "page2", 
                    "title": "Page 2",
                    "content": "Content of page 2",
                    "filePaths": ["file2.py"],
                    "importance": "medium",
                    "relatedPages": ["page1"]
                }
            ],
            "sections": [],
            "rootSections": []
        },
        "generated_pages": {
            "page1": {
                "id": "page1",
                "title": "Page 1", 
                "content": "Content of page 1",
                "filePaths": ["file1.py"],
                "importance": "high",
                "relatedPages": ["page2"]
            }
        },
        "repo": {
            "owner": "testuser",
            "repo": "testrepo", 
            "type": "github",
            "token": None,
            "localPath": None,
            "repoUrl": "https://github.com/testuser/testrepo"
        },
        "provider": "google",
        "model": "gemini-2.5-flash"
    }


@pytest.fixture
def mock_file_system():
    """Mock file system operations for testing."""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('os.walk') as mock_walk, \
         patch('builtins.open', create=True) as mock_open:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['test_file.py', 'test_file2.py']
        mock_walk.return_value = [
            ('/test/path', ['subdir'], ['file1.py', 'file2.py']),
            ('/test/path/subdir', [], ['file3.py'])
        ]
        
        yield {
            'exists': mock_exists,
            'listdir': mock_listdir,
            'walk': mock_walk,
            'open': mock_open
        }


@pytest.fixture
def sample_repo_structure():
    """Sample repository structure for testing."""
    return {
        "name": "test-repo",
        "description": "A test repository",
        "files": [
            {
                "path": "main.py",
                "content": "print('Hello, World!')",
                "language": "python"
            },
            {
                "path": "README.md",
                "content": "# Test Repository\n\nThis is a test.",
                "language": "markdown"
            },
            {
                "path": "requirements.txt",
                "content": "fastapi>=0.95.0\npydantic>=2.0.0",
                "language": "text"
            }
        ],
        "structure": {
            "directories": ["tests", "src"],
            "files": ["main.py", "README.md", "requirements.txt"]
        }
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests."""
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that test component interactions"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests that test complete workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take more than a few seconds to run"
    )
    config.addinivalue_line(
        "markers", "network: Tests that require network access"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: Tests that require real API keys"
    )