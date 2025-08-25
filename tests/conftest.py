"""
Simplified pytest configuration and fixtures for basic testing.
"""

import os
import pytest
import tempfile
import shutil
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

# Set test environment variables before importing modules
os.environ["TESTING"] = "1"
os.environ["GOOGLE_API_KEY"] = "test_google_key"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["OPENROUTER_API_KEY"] = "test_openrouter_key"


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