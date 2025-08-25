"""
Unit tests for configuration module.
"""

import pytest
import os
import json
from unittest.mock import patch, mock_open, Mock
from pathlib import Path

from api.config import (
    load_json_config,
    replace_env_placeholders,
    get_model_config,
    load_generator_config,
    load_embedder_config,
    is_ollama_embedder,
    CLIENT_CLASSES
)


@pytest.mark.unit
class TestConfigModule:
    """Test suite for configuration module."""
    
    def test_replace_env_placeholders_with_valid_env_var(self):
        """Test replacing environment variable placeholders."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = {
                "key1": "${TEST_VAR}",
                "key2": "prefix_${TEST_VAR}_suffix",
                "nested": {
                    "key3": "${TEST_VAR}"
                }
            }
            
            result = replace_env_placeholders(config)
            
            assert result["key1"] == "test_value"
            assert result["key2"] == "prefix_test_value_suffix"
            assert result["nested"]["key3"] == "test_value"

    def test_replace_env_placeholders_with_missing_env_var(self, caplog):
        """Test handling of missing environment variables."""
        config = {
            "key1": "${MISSING_VAR}",
            "key2": "normal_value"
        }
        
        result = replace_env_placeholders(config)
        
        assert result["key1"] == "${MISSING_VAR}"  # Should remain unchanged
        assert result["key2"] == "normal_value"
        assert "Environment variable placeholder" in caplog.text

    def test_replace_env_placeholders_with_list(self):
        """Test replacing placeholders in lists."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = ["${TEST_VAR}", "normal_value", {"nested": "${TEST_VAR}"}]
            
            result = replace_env_placeholders(config)
            
            assert result[0] == "test_value"
            assert result[1] == "normal_value"
            assert result[2]["nested"] == "test_value"

    def test_replace_env_placeholders_with_non_string_values(self):
        """Test that non-string values are not affected."""
        config = {
            "number": 42,
            "boolean": True,
            "null": None,
            "float": 3.14
        }
        
        result = replace_env_placeholders(config)
        
        assert result == config

    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "value"}')
    @patch('pathlib.Path.exists')
    def test_load_json_config_success(self, mock_exists, mock_file):
        """Test successful JSON configuration loading."""
        mock_exists.return_value = True
        
        result = load_json_config("test.json")
        
        assert result == {"test": "value"}
        mock_file.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_json_config_file_not_exists(self, mock_exists, caplog):
        """Test handling when config file doesn't exist."""
        mock_exists.return_value = False
        
        result = load_json_config("nonexistent.json")
        
        assert result == {}
        assert "does not exist" in caplog.text

    @patch('builtins.open', side_effect=Exception("File read error"))
    @patch('pathlib.Path.exists')
    def test_load_json_config_error_handling(self, mock_exists, mock_file, caplog):
        """Test error handling during config loading."""
        mock_exists.return_value = True
        
        result = load_json_config("error.json")
        
        assert result == {}
        assert "Error loading configuration file" in caplog.text

    def test_get_model_config_google_provider(self):
        """Test getting model configuration for Google provider."""
        mock_configs = {
            "providers": {
                "google": {
                    "model_client": "MockClient",
                    "default_model": "gemini-pro",
                    "models": {
                        "gemini-pro": {
                            "temperature": 0.7,
                            "max_tokens": 1000
                        }
                    }
                }
            }
        }
        
        with patch('api.config.configs', mock_configs):
            config = get_model_config("google", "gemini-pro")
            
            assert config["model_client"] == "MockClient"
            assert config["model_kwargs"]["model"] == "gemini-pro"
            assert config["model_kwargs"]["temperature"] == 0.7

    def test_get_model_config_ollama_provider(self):
        """Test getting model configuration for Ollama provider."""
        mock_configs = {
            "providers": {
                "ollama": {
                    "model_client": "OllamaClient",
                    "default_model": "llama2",
                    "models": {
                        "llama2": {
                            "options": {
                                "temperature": 0.8,
                                "num_predict": 500
                            }
                        }
                    }
                }
            }
        }
        
        with patch('api.config.configs', mock_configs):
            config = get_model_config("ollama", "llama2")
            
            assert config["model_client"] == "OllamaClient"
            assert config["model_kwargs"]["model"] == "llama2"
            assert config["model_kwargs"]["temperature"] == 0.8

    def test_get_model_config_provider_not_found(self):
        """Test error when provider is not found."""
        mock_configs = {"providers": {}}
        
        with patch('api.config.configs', mock_configs):
            with pytest.raises(ValueError, match="Configuration for provider 'nonexistent' not found"):
                get_model_config("nonexistent")

    def test_get_model_config_no_providers(self):
        """Test error when no providers are configured."""
        mock_configs = {}
        
        with patch('api.config.configs', mock_configs):
            with pytest.raises(ValueError, match="Provider configuration not loaded"):
                get_model_config("google")

    def test_is_ollama_embedder_true(self):
        """Test is_ollama_embedder returns True for OllamaClient."""
        mock_configs = {
            "embedder": {
                "model_client": Mock(__name__="OllamaClient")
            }
        }
        
        with patch('api.config.configs', mock_configs):
            assert is_ollama_embedder() is True

    def test_is_ollama_embedder_false(self):
        """Test is_ollama_embedder returns False for non-OllamaClient."""
        mock_configs = {
            "embedder": {
                "model_client": Mock(__name__="OpenAIClient")
            }
        }
        
        with patch('api.config.configs', mock_configs):
            assert is_ollama_embedder() is False

    def test_is_ollama_embedder_fallback_to_client_class(self):
        """Test fallback to client_class when model_client not available."""
        mock_configs = {
            "embedder": {
                "client_class": "OllamaClient"
            }
        }
        
        with patch('api.config.configs', mock_configs):
            assert is_ollama_embedder() is True

    def test_is_ollama_embedder_no_config(self):
        """Test is_ollama_embedder with no embedder config."""
        mock_configs = {}
        
        with patch('api.config.configs', mock_configs):
            assert is_ollama_embedder() is False

    def test_client_classes_mapping(self):
        """Test that CLIENT_CLASSES contains expected mappings."""
        assert "GoogleGenAIClient" in CLIENT_CLASSES
        assert "OpenAIClient" in CLIENT_CLASSES
        assert "OpenRouterClient" in CLIENT_CLASSES
        assert "OllamaClient" in CLIENT_CLASSES
        assert "BedrockClient" in CLIENT_CLASSES
        assert "AzureAIClient" in CLIENT_CLASSES
        assert "DashscopeClient" in CLIENT_CLASSES

    @patch('api.config.load_json_config')
    def test_load_generator_config(self, mock_load_json):
        """Test loading generator configuration."""
        mock_config = {
            "default_provider": "google",
            "providers": {
                "google": {
                    "client_class": "GoogleGenAIClient"
                }
            }
        }
        mock_load_json.return_value = mock_config
        
        result = load_generator_config()
        
        assert result["default_provider"] == "google"
        assert "model_client" in result["providers"]["google"]

    @patch('api.config.load_json_config')
    def test_load_embedder_config(self, mock_load_json):
        """Test loading embedder configuration."""
        mock_config = {
            "embedder": {
                "client_class": "OpenAIClient"
            }
        }
        mock_load_json.return_value = mock_config
        
        result = load_embedder_config()
        
        assert "model_client" in result["embedder"]