"""
Unit tests for WikiGenerator module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from api.wiki_generator import WikiGenerator


@pytest.fixture
def wiki_generator():
    """Create WikiGenerator instance for testing."""
    return WikiGenerator(provider="google", model="gemini-2.5-flash")


@pytest.fixture
def sample_repository_structure():
    """Sample repository structure for testing."""
    return {
        "files": [
            {"path": "main.py", "content": "def main(): pass", "language": "python"},
            {"path": "README.md", "content": "# Test Repo", "language": "markdown"},
            {"path": "config.json", "content": '{"test": true}', "language": "json"}
        ],
        "structure": {
            "python_files": ["main.py"],
            "documentation": ["README.md"],
            "config_files": ["config.json"]
        }
    }


@pytest.mark.unit
class TestWikiGenerator:
    """Test suite for WikiGenerator."""
    
    def test_wiki_generator_initialization(self):
        """Test WikiGenerator initialization."""
        generator = WikiGenerator(provider="google", model="gemini-2.5-flash")
        assert generator.provider == "google"
        assert generator.model == "gemini-2.5-flash"

    def test_wiki_generator_default_initialization(self):
        """Test WikiGenerator initialization with defaults."""
        generator = WikiGenerator()
        assert generator.provider == "google"
        assert generator.model is None

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_analyze_repository(self, mock_get_client, wiki_generator, temp_repo_dir):
        """Test repository analysis functionality."""
        # Create test files in temp directory
        test_files = {
            "main.py": "def main():\n    print('Hello World')\n",
            "README.md": "# Test Repository\n\nThis is a test.",
            "requirements.txt": "fastapi>=0.95.0\n"
        }
        
        for filename, content in test_files.items():
            with open(os.path.join(temp_repo_dir, filename), 'w') as f:
                f.write(content)
        
        # Mock the model client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        result = wiki_generator._analyze_repository(temp_repo_dir)
        
        assert result is not None
        assert isinstance(result, dict)

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_architecture_diagram(self, mock_get_client, wiki_generator, sample_repository_structure):
        """Test architecture diagram generation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        diagram = wiki_generator._generate_architecture_diagram(sample_repository_structure)
        
        assert isinstance(diagram, str)
        assert "graph" in diagram.lower() or "flowchart" in diagram.lower()

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_data_flow_diagram(self, mock_get_client, wiki_generator, sample_repository_structure):
        """Test data flow diagram generation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        diagram = wiki_generator._generate_data_flow_diagram(sample_repository_structure)
        
        assert isinstance(diagram, str)
        assert len(diagram) > 0

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_api_flow_diagram(self, mock_get_client, wiki_generator, sample_repository_structure):
        """Test API flow diagram generation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        diagram = wiki_generator._generate_api_flow_diagram(sample_repository_structure)
        
        assert isinstance(diagram, str)
        assert len(diagram) > 0

    @patch('api.wiki_generator.WikiGenerator._analyze_repository')
    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_wiki_structure(self, mock_get_client, mock_analyze, wiki_generator, temp_repo_dir):
        """Test complete wiki structure generation."""
        # Mock repository analysis
        mock_analyze.return_value = {
            "files": ["main.py", "README.md"],
            "structure": {"python_files": ["main.py"]}
        }
        
        # Mock model client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"title": "Test Wiki", "pages": []}'
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = wiki_generator.generate_wiki_structure(
            repo_path=temp_repo_dir,
            repo_url="https://github.com/test/repo",
            language="en"
        )
        
        assert result is not None
        assert isinstance(result, dict)

    def test_get_model_client_google(self, wiki_generator):
        """Test getting Google model client."""
        with patch('api.wiki_generator.get_model_config') as mock_config:
            mock_config.return_value = {
                "model_client": Mock(),
                "model_kwargs": {"model": "gemini-2.5-flash"}
            }
            
            client = wiki_generator._get_model_client()
            assert client is not None

    def test_get_model_client_error_handling(self, wiki_generator):
        """Test error handling when getting model client fails."""
        with patch('api.wiki_generator.get_model_config') as mock_config:
            mock_config.side_effect = ValueError("Provider not found")
            
            with pytest.raises(ValueError):
                wiki_generator._get_model_client()

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_extract_file_information(self, mock_get_client, wiki_generator):
        """Test file information extraction."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        test_content = "def hello():\n    return 'Hello World'"
        
        info = wiki_generator._extract_file_information("test.py", test_content)
        
        assert isinstance(info, dict)
        assert "filename" in info or "content" in info

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_page_content(self, mock_get_client, wiki_generator):
        """Test wiki page content generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "# Test Page\n\nThis is test content."
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        content = wiki_generator._generate_page_content(
            page_title="Test Page",
            file_paths=["test.py"],
            context="Test context"
        )
        
        assert isinstance(content, str)
        assert len(content) > 0

    def test_validate_mermaid_syntax(self, wiki_generator):
        """Test Mermaid diagram syntax validation."""
        valid_diagram = "graph TD\n    A --> B"
        invalid_diagram = "invalid mermaid syntax"
        
        assert wiki_generator._validate_mermaid_syntax(valid_diagram) is True
        assert wiki_generator._validate_mermaid_syntax(invalid_diagram) is False

    def test_sanitize_diagram_output(self, wiki_generator):
        """Test diagram output sanitization."""
        raw_output = "```mermaid\ngraph TD\n    A --> B\n```"
        expected = "graph TD\n    A --> B"
        
        result = wiki_generator._sanitize_diagram_output(raw_output)
        assert result == expected

    def test_extract_file_dependencies(self, wiki_generator):
        """Test file dependency extraction."""
        python_content = "import os\nfrom typing import Dict\nimport custom_module"
        
        dependencies = wiki_generator._extract_file_dependencies("test.py", python_content)
        
        assert isinstance(dependencies, list)
        assert any("os" in dep for dep in dependencies)

    @patch('api.wiki_generator.WikiGenerator._get_model_client')
    def test_generate_section_overview(self, mock_get_client, wiki_generator):
        """Test section overview generation."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "This section covers the main application logic."
        mock_client.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        overview = wiki_generator._generate_section_overview(
            section_name="Core Logic",
            files=["main.py", "utils.py"]
        )
        
        assert isinstance(overview, str)
        assert len(overview) > 0

    def test_categorize_files_by_type(self, wiki_generator):
        """Test file categorization by type."""
        files = [
            "main.py",
            "test_main.py", 
            "README.md",
            "config.json",
            "requirements.txt",
            "script.js",
            "style.css"
        ]
        
        categories = wiki_generator._categorize_files_by_type(files)
        
        assert "python" in categories
        assert "documentation" in categories
        assert "configuration" in categories
        assert "main.py" in categories["python"]
        assert "README.md" in categories["documentation"]