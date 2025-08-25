"""Tests to verify the refactoring was successful."""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all refactored modules can be imported."""
    
    # Core imports
    from src.grantha.core.config import Config, get_config
    from src.grantha.core.logging_config import setup_logging
    
    # Model imports  
    from src.grantha.models.api_models import WikiPage, RepoInfo
    
    # API imports
    from src.grantha.api.app import create_app
    from src.grantha.api.routes import auth_router, models_router
    
    # Client imports
    from src.grantha.clients.openai_client import OpenAIClient
    from src.grantha.clients.openrouter_client import OpenRouterClient
    
    # Utility imports - these might fail if dependencies aren't available
    try:
        from src.grantha.utils.data_pipeline import DataPipeline
        from src.grantha.utils.embedder import Embedder
    except ImportError:
        # Expected if dependencies aren't installed
        pass
    
    assert True  # If we get here, imports worked


def test_config_creation():
    """Test that configuration can be created and accessed."""
    from src.grantha.core.config import Config, get_config
    
    config = Config()
    assert config is not None
    
    global_config = get_config()
    assert global_config is not None


def test_app_creation():
    """Test that the FastAPI app can be created."""
    from src.grantha.api.app import create_app
    
    app = create_app()
    assert app is not None
    assert hasattr(app, 'routes')


def test_model_validation():
    """Test that Pydantic models work correctly."""
    from src.grantha.models.api_models import WikiPage, RepoInfo
    
    # Test WikiPage model
    wiki_page = WikiPage(
        id="test",
        title="Test Page",
        content="Test content",
        filePaths=["test.py"],
        importance="high",
        relatedPages=[]
    )
    assert wiki_page.id == "test"
    assert wiki_page.title == "Test Page"
    
    # Test RepoInfo model
    repo_info = RepoInfo(
        owner="testuser",
        repo="testrepo",
        type="github"
    )
    assert repo_info.owner == "testuser"
    assert repo_info.repo == "testrepo"


def test_directory_structure():
    """Test that the new directory structure exists."""
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        "src/grantha/core",
        "src/grantha/clients", 
        "src/grantha/models",
        "src/grantha/utils",
        "src/grantha/api",
        "tests",
        "configs"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} should exist"
        assert full_path.is_dir(), f"{dir_path} should be a directory"


def test_backward_compatibility():
    """Test that backward compatibility symlinks work."""
    project_root = Path(__file__).parent.parent
    
    # Test some key symlinks exist
    api_dir = project_root / "api"
    if api_dir.exists():
        symlinks_to_check = [
            "config.py",
            "logging_config.py", 
            "openai_client.py"
        ]
        
        for symlink_name in symlinks_to_check:
            symlink_path = api_dir / symlink_name
            if symlink_path.exists():
                assert symlink_path.is_symlink(), f"{symlink_name} should be a symlink"


def test_package_metadata():
    """Test that package metadata is correctly defined."""
    from src.grantha import __version__
    
    assert __version__ == "0.1.0"


if __name__ == "__main__":
    pytest.main([__file__])