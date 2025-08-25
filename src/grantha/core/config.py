"""Configuration management for the Grantha platform."""

import os
import json
import logging
import re
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Central configuration class for Grantha platform."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    aws_role_arn: Optional[str] = None
    
    # Application Settings
    wiki_auth_mode: bool = False
    wiki_auth_code: str = ""
    config_dir: Optional[str] = None
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.environ.get('AWS_REGION')
        self.aws_role_arn = os.environ.get('AWS_ROLE_ARN')
        
        # Wiki authentication settings
        raw_auth_mode = os.environ.get('GRANTHA_AUTH_MODE', 'False')
        self.wiki_auth_mode = raw_auth_mode.lower() in ['true', '1', 't']
        self.wiki_auth_code = os.environ.get('GRANTHA_AUTH_CODE', '')
        
        # Configuration directory
        self.config_dir = os.environ.get('GRANTHA_CONFIG_DIR', None)
        
        # Set environment variables (for backward compatibility)
        self._set_env_vars()
    
    def _set_env_vars(self):
        """Set environment variables for backward compatibility."""
        env_mappings = {
            'OPENAI_API_KEY': self.openai_api_key,
            'GOOGLE_API_KEY': self.google_api_key,
            'OPENROUTER_API_KEY': self.openrouter_api_key,
            'AWS_ACCESS_KEY_ID': self.aws_access_key_id,
            'AWS_SECRET_ACCESS_KEY': self.aws_secret_access_key,
            'AWS_REGION': self.aws_region,
            'AWS_ROLE_ARN': self.aws_role_arn
        }
        
        for key, value in env_mappings.items():
            if value:
                os.environ[key] = value


class ConfigLoader:
    """Configuration loader with environment variable substitution."""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Client class mapping (lazy import to avoid circular dependencies)
        self._client_classes = None
    
    @property
    def client_classes(self) -> Dict[str, Any]:
        """Get client classes with lazy loading."""
        if self._client_classes is None:
            # Import clients here to avoid circular imports
            try:
                from ..clients.openai_client import OpenAIClient
                from ..clients.openrouter_client import OpenRouterClient
                from ..clients.bedrock_client import BedrockClient
                from ..clients.azureai_client import AzureAIClient
                from ..clients.dashscope_client import DashscopeClient
                from adalflow import GoogleGenAIClient, OllamaClient
                
                self._client_classes = {
                    "GoogleGenAIClient": GoogleGenAIClient,
                    "OpenAIClient": OpenAIClient,
                    "OpenRouterClient": OpenRouterClient,
                    "OllamaClient": OllamaClient,
                    "BedrockClient": BedrockClient,
                    "AzureAIClient": AzureAIClient,
                    "DashscopeClient": DashscopeClient
                }
            except ImportError as e:
                logger.warning(f"Could not import all client classes: {e}")
                self._client_classes = {}
                
        return self._client_classes
    
    def replace_env_placeholders(self, config_obj: Union[Dict[str, Any], List[Any], str, Any]) -> Union[Dict[str, Any], List[Any], str, Any]:
        """
        Recursively replace placeholders like "${ENV_VAR}" in string values
        within a nested configuration structure with environment variable values.
        """
        pattern = re.compile(r"\$\{([A-Z0-9_]+)\}")

        def replacer(match: re.Match[str]) -> str:
            env_var_name = match.group(1)
            original_placeholder = match.group(0)
            env_var_value = os.environ.get(env_var_name)
            if env_var_value is None:
                logger.warning(
                    f"Environment variable placeholder '{original_placeholder}' was not found. "
                    f"Using placeholder as is."
                )
                return original_placeholder
            return env_var_value

        if isinstance(config_obj, dict):
            return {k: self.replace_env_placeholders(v) for k, v in config_obj.items()}
        elif isinstance(config_obj, list):
            return [self.replace_env_placeholders(item) for item in config_obj]
        elif isinstance(config_obj, str):
            return pattern.sub(replacer, config_obj)
        else:
            return config_obj

    def load_json_config(self, filename: str) -> Dict[str, Any]:
        """Load and process JSON configuration file."""
        try:
            # Determine config path
            if self.config.config_dir:
                config_path = Path(self.config.config_dir) / filename
            else:
                # Default to config directory relative to this file
                config_path = Path(__file__).parent.parent.parent.parent / "configs" / filename

            logger.info(f"Loading configuration from {config_path}")

            if not config_path.exists():
                logger.warning(f"Configuration file {config_path} does not exist")
                return {}

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                return self.replace_env_placeholders(config_data)
                
        except Exception as e:
            logger.error(f"Error loading configuration file {filename}: {str(e)}")
            return {}

    def load_generator_config(self) -> Dict[str, Any]:
        """Load generator model configuration."""
        generator_config = self.load_json_config("generator.json")

        # Add client classes to each provider
        if "providers" in generator_config:
            for provider_id, provider_config in generator_config["providers"].items():
                # Try to set client class from client_class
                client_class_name = provider_config.get("client_class")
                if client_class_name and client_class_name in self.client_classes:
                    provider_config["model_client"] = self.client_classes[client_class_name]
                # Fall back to default mapping based on provider_id
                elif provider_id in ["google", "openai", "openrouter", "ollama", "bedrock", "azure", "dashscope"]:
                    default_map = {
                        "google": "GoogleGenAIClient",
                        "openai": "OpenAIClient",
                        "openrouter": "OpenRouterClient",
                        "ollama": "OllamaClient",
                        "bedrock": "BedrockClient",
                        "azure": "AzureAIClient",
                        "dashscope": "DashscopeClient"
                    }
                    client_class_name = default_map.get(provider_id)
                    if client_class_name and client_class_name in self.client_classes:
                        provider_config["model_client"] = self.client_classes[client_class_name]
                else:
                    logger.warning(f"Unknown provider or client class: {provider_id}")

        return generator_config

    def load_embedder_config(self) -> Dict[str, Any]:
        """Load embedder configuration."""
        embedder_config = self.load_json_config("embedder.json")

        # Process client classes
        for key in ["embedder", "embedder_ollama"]:
            if key in embedder_config and "client_class" in embedder_config[key]:
                class_name = embedder_config[key]["client_class"]
                if class_name in self.client_classes:
                    embedder_config[key]["model_client"] = self.client_classes[class_name]

        return embedder_config

    def load_repo_config(self) -> Dict[str, Any]:
        """Load repository and file filters configuration."""
        return self.load_json_config("repo.json")

    def load_lang_config(self) -> Dict[str, Any]:
        """Load language configuration."""
        default_config = {
            "supported_languages": {
                "en": "English",
                "ja": "Japanese (日本語)",
                "zh": "Mandarin Chinese (中文)",
                "zh-tw": "Traditional Chinese (繁體中文)",
                "es": "Spanish (Español)",
                "kr": "Korean (한국어)",
                "vi": "Vietnamese (Tiếng Việt)",
                "pt-br": "Brazilian Portuguese (Português Brasileiro)",
                "fr": "Français (French)",
                "de": "German (Deutsch)",
                "it": "Italian (Italiano)",
                "ru": "Russian (Русский)",
                "ar": "Arabic (العربية)",
                "hi": "Hindi (हिन्दी)",
                "th": "Thai (ไทย)",
                "tr": "Turkish (Türkçe)",
                "pl": "Polish (Polski)",
                "nl": "Dutch (Nederlands)",
                "sv": "Swedish (Svenska)",
                "da": "Danish (Dansk)",
                "no": "Norwegian (Norsk)",
                "fi": "Finnish (Suomi)",
                "cs": "Czech (Čeština)",
                "hu": "Hungarian (Magyar)",
                "ro": "Romanian (Română)",
                "bg": "Bulgarian (Български)",
                "hr": "Croatian (Hrvatski)",
                "sk": "Slovak (Slovenčina)",
                "sl": "Slovenian (Slovenščina)",
                "et": "Estonian (Eesti)",
                "lv": "Latvian (Latviešu)",
                "lt": "Lithuanian (Lietuvių)",
                "uk": "Ukrainian (Українська)",
                "he": "Hebrew (עברית)",
                "fa": "Persian (فارسی)",
                "ur": "Urdu (اردو)",
                "bn": "Bengali (বাংলা)",
                "ta": "Tamil (தமிழ்)",
                "te": "Telugu (తెలుగు)",
                "ml": "Malayalam (മലയാളം)",
                "kn": "Kannada (ಕನ್ನಡ)",
                "gu": "Gujarati (ગુજરાતી)",
                "mr": "Marathi (मराठी)",
                "pa": "Punjabi (ਪੰਜਾਬੀ)",
                "or": "Odia (ଓଡ଼ିଆ)",
                "as": "Assamese (অসমীয়া)",
                "ne": "Nepali (नेपाली)",
                "si": "Sinhala (සිංහල)",
                "my": "Burmese (မြန်မာ)",
                "km": "Khmer (ខ្មែរ)",
                "lo": "Lao (ລາວ)",
                "ka": "Georgian (ქართული)",
                "am": "Amharic (አማርኛ)",
                "sw": "Swahili (Kiswahili)",
                "zu": "Zulu (isiZulu)",
                "af": "Afrikaans",
                "is": "Icelandic (Íslenska)",
                "mt": "Maltese (Malti)",
                "cy": "Welsh (Cymraeg)",
                "ga": "Irish (Gaeilge)",
                "gd": "Scottish Gaelic (Gàidhlig)",
                "br": "Breton (Brezhoneg)",
                "eu": "Basque (Euskera)",
                "ca": "Catalan (Català)",
                "gl": "Galician (Galego)",
                "oc": "Occitan",
                "co": "Corsican (Corsu)",
                "sc": "Sardinian (Sardu)",
                "rm": "Romansh (Rumantsch)",
                "lb": "Luxembourgish (Lëtzebuergesch)",
                "fo": "Faroese (Føroyskt)",
                "kl": "Greenlandic (Kalaallisut)"
            },
            "default_language": "en"
        }
        
        lang_config = self.load_json_config("lang.json")
        if not lang_config:
            return default_config
        return lang_config


# Global configuration instance
_config = Config()
_config_loader = ConfigLoader(_config)

# Global configs cache
configs = {
    "generator": _config_loader.load_generator_config(),
    "embedder": _config_loader.load_embedder_config(),
    "repo": _config_loader.load_repo_config(),
    "lang": _config_loader.load_lang_config()
}


def get_config() -> Config:
    """Get the global configuration instance."""
    return _config


def get_embedder_config() -> Dict[str, Any]:
    """Get the current embedder configuration."""
    return configs.get("embedder", {})


def is_ollama_embedder() -> bool:
    """Check if the current embedder configuration uses OllamaClient."""
    embedder_config = get_embedder_config()
    if not embedder_config:
        return False

    # Check if model_client is OllamaClient
    model_client = embedder_config.get("model_client")
    if model_client:
        return model_client.__name__ == "OllamaClient"

    # Fallback: check client_class string
    client_class = embedder_config.get("client_class", "")
    return client_class == "OllamaClient"


# Default excluded directories and files for backward compatibility
DEFAULT_EXCLUDED_DIRS: List[str] = [
    # Virtual environments and package managers
    "./.venv/", "./venv/", "./env/", "./virtualenv/",
    "./node_modules/", "./bower_components/", "./jspm_packages/",
    # Version control
    "./.git/", "./.svn/", "./.hg/", "./.bzr/",
    # Cache and compiled files
    "./__pycache__/", "./.pytest_cache/", "./.mypy_cache/", "./.ruff_cache/", "./.coverage/",
    # Build and distribution
    "./dist/", "./build/", "./out/", "./target/", "./bin/", "./obj/",
    # Documentation
    "./docs/", "./_docs/", "./site-docs/", "./_site/",
    # IDE specific
    "./.idea/", "./.vscode/", "./.vs/", "./.eclipse/", "./.settings/",
    # Logs and temporary files
    "./logs/", "./log/", "./tmp/", "./temp/",
]

DEFAULT_EXCLUDED_FILES: List[str] = [
    "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json", "poetry.lock",
    "Pipfile.lock", "requirements.txt.lock", "Cargo.lock", "composer.lock",
    ".lock", ".DS_Store", "Thumbs.db", "desktop.ini", "*.lnk", ".env",
    ".env.*", "*.env", "*.cfg", "*.ini", ".flaskenv", ".gitignore",
    ".gitattributes", ".gitmodules", ".github", ".gitlab-ci.yml",
    ".prettierrc", ".eslintrc", ".eslintignore", ".stylelintrc",
    ".editorconfig", ".jshintrc", ".pylintrc", ".flake8", "mypy.ini",
    "pyproject.toml", "tsconfig.json", "webpack.config.js", "babel.config.js",
    "rollup.config.js", "jest.config.js", "karma.conf.js", "vite.config.js",
    "next.config.js", "*.min.js", "*.min.css", "*.bundle.js", "*.bundle.css",
    "*.map", "*.gz", "*.zip", "*.tar", "*.tgz", "*.rar", "*.7z", "*.iso",
    "*.dmg", "*.img", "*.msix", "*.appx", "*.appxbundle", "*.xap", "*.ipa",
    "*.deb", "*.rpm", "*.msi", "*.exe", "*.dll", "*.so", "*.dylib", "*.o",
    "*.a", "*.lib", "*.pdb", "*.ilk", "*.exp", "*.obj", "*.pyc", "*.pyo",
    "*.class", "*.jar", "*.war", "*.ear", "*.aar", "*.apk", "*.xcarchive",
    "*.ipa", "*.app", "*.whl", "*.egg", "*.sdist", "*.dmg",
]

# Legacy compatibility constants 
WIKI_AUTH_MODE = _config.wiki_auth_mode
WIKI_AUTH_CODE = _config.wiki_auth_code


def reload_configs():
    """Reload all configurations."""
    global configs
    configs = {
        "generator": _config_loader.load_generator_config(),
        "embedder": _config_loader.load_embedder_config(), 
        "repo": _config_loader.load_repo_config(),
        "lang": _config_loader.load_lang_config()
    }