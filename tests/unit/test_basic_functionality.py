"""
Basic functionality tests that don't require complex imports.
"""

import pytest
import os
import json
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestBasicFunctionality:
    """Basic test suite to verify testing infrastructure."""
    
    def test_environment_setup(self):
        """Test that test environment is properly set up."""
        # Test environment variable should be set
        assert os.environ.get("TESTING") == "1"
        
    def test_mock_functionality(self):
        """Test that mocking works correctly."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
            
            # Simulate file reading
            with open("dummy_file.json", "r") as f:
                content = f.read()
                data = json.loads(content)
                
            assert data["test"] == "data"
            mock_open.assert_called_once_with("dummy_file.json", "r")
    
    def test_pytest_marks(self):
        """Test that pytest markers work correctly."""
        # This test should be marked as 'unit'
        # The marker is applied at the class level
        pass
    
    def test_basic_assertions(self):
        """Test basic assertion functionality."""
        assert 1 + 1 == 2
        assert "hello" in "hello world"
        assert len([1, 2, 3]) == 3
        
        # Test with mock
        mock_obj = Mock()
        mock_obj.method.return_value = "mocked"
        
        result = mock_obj.method()
        assert result == "mocked"
        mock_obj.method.assert_called_once()
    
    def test_exception_handling(self):
        """Test exception handling in tests."""
        with pytest.raises(ValueError):
            raise ValueError("Test exception")
            
        with pytest.raises(KeyError):
            empty_dict = {}
            _ = empty_dict["missing_key"]
    
    def test_parameterized_input(self):
        """Test handling different input types."""
        test_cases = [
            ("string", str),
            (42, int),
            (3.14, float),
            ([1, 2, 3], list),
            ({"key": "value"}, dict)
        ]
        
        for value, expected_type in test_cases:
            assert isinstance(value, expected_type)
    
    def test_json_operations(self):
        """Test JSON operations."""
        test_data = {
            "name": "Test Project",
            "version": "1.0.0",
            "features": ["feature1", "feature2"],
            "config": {
                "debug": True,
                "port": 8000
            }
        }
        
        # Test serialization
        json_str = json.dumps(test_data)
        assert isinstance(json_str, str)
        assert "Test Project" in json_str
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        assert parsed_data == test_data
        assert parsed_data["name"] == "Test Project"
        assert parsed_data["config"]["debug"] is True
    
    def test_string_operations(self):
        """Test string operations commonly used in the project."""
        test_string = "  Hello, Grantha API!  "
        
        # Test string cleaning
        cleaned = test_string.strip()
        assert cleaned == "Hello, Grantha API!"
        
        # Test string formatting
        formatted = f"Welcome to {cleaned}"
        assert formatted == "Welcome to Hello, Grantha API!"
        
        # Test string manipulation
        words = cleaned.split(", ")
        assert len(words) == 2
        assert words[0] == "Hello"
        assert "Grantha API!" in words[1]
    
    def test_list_operations(self):
        """Test list operations."""
        test_list = [1, 2, 3, 4, 5]
        
        # Test filtering
        even_numbers = [x for x in test_list if x % 2 == 0]
        assert even_numbers == [2, 4]
        
        # Test mapping
        squared = [x ** 2 for x in test_list]
        assert squared == [1, 4, 9, 16, 25]
        
        # Test aggregation
        total = sum(test_list)
        assert total == 15
    
    def test_dictionary_operations(self):
        """Test dictionary operations."""
        test_dict = {
            "api": "grantha",
            "version": "1.0.0",
            "endpoints": ["health", "wiki", "export"]
        }
        
        # Test key access
        assert test_dict["api"] == "grantha"
        assert test_dict.get("missing_key", "default") == "default"
        
        # Test key iteration
        keys = list(test_dict.keys())
        assert "api" in keys
        assert "version" in keys
        
        # Test value modification
        test_dict["version"] = "1.1.0"
        assert test_dict["version"] == "1.1.0"
    
    @patch.dict(os.environ, {"TEST_ENV_VAR": "test_value"})
    def test_environment_variables(self):
        """Test environment variable handling."""
        assert os.environ.get("TEST_ENV_VAR") == "test_value"
        
        # Test with default value
        assert os.environ.get("NON_EXISTENT", "default") == "default"