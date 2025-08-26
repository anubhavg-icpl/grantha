"""Configuration management for the Grantha platform."""

import os
import json
import logging
import re
from pathlib import Path
from typing import List, Union, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Load environment variables from unified .env file
try:
    from dotenv import load_dotenv
    # Load from project root .env file
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        logging.info(f"Loaded unified environment from {env_path}")
except ImportError:
    logging.warning("python-dotenv not installed, skipping .env loading")

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
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    frontend_port: int = 3000
    frontend_host: str = "0.0.0.0"
    server_base_url: str = "http://localhost:8000"
    api_base_url: str = "http://localhost:8000/api"
    ws_url: str = "ws://localhost:8000/ws"
    
    # Application Settings
    app_name: str = "Grantha"
    app_version: str = "1.0.0"
    app_description: str = "Advanced AI Platform for Documentation, Chat, and Research"
    
    # Environment
    node_env: str = "development"
    python_env: str = "development"
    
    # Security
    secret_key: str = "grantha_dev_secret_change_in_production"
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ])
    
    # Feature Flags
    enable_agents: bool = True
    enable_research: bool = True
    enable_wiki: bool = True
    enable_simple: bool = True
    enable_chat: bool = True
    
    # Legacy Settings
    wiki_auth_mode: bool = False
    wiki_auth_code: str = ""
    config_dir: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/grantha.log"
    
    # AI Model Configuration
    default_model: str = "gpt-4"
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    default_embedding_model: str = "text-embedding-ada-002"
    
    # Build & Development
    debug: bool = False
    build_version: str = "1.0.0"
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        # API Keys
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_API_KEY')
        self.openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
        self.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.environ.get('AWS_REGION')
        self.aws_role_arn = os.environ.get('AWS_ROLE_ARN')
        self.azure_openai_api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        self.azure_openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
        self.dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY')
        
        # Server Configuration
        self.api_host = os.environ.get('API_HOST', self.api_host)
        self.api_port = int(os.environ.get('API_PORT', self.api_port))
        self.api_reload = os.environ.get('API_RELOAD', str(self.api_reload)).lower() in ['true', '1', 't']
        self.frontend_port = int(os.environ.get('FRONTEND_PORT', self.frontend_port))
        self.frontend_host = os.environ.get('FRONTEND_HOST', self.frontend_host)
        self.server_base_url = os.environ.get('SERVER_BASE_URL', self.server_base_url)
        self.api_base_url = os.environ.get('API_BASE_URL', self.api_base_url)
        self.ws_url = os.environ.get('WS_URL', self.ws_url)
        
        # Application Settings
        self.app_name = os.environ.get('APP_NAME', self.app_name)
        self.app_version = os.environ.get('APP_VERSION', self.app_version)
        self.app_description = os.environ.get('APP_DESCRIPTION', self.app_description)
        
        # Environment
        self.node_env = os.environ.get('NODE_ENV', self.node_env)
        self.python_env = os.environ.get('PYTHON_ENV', self.python_env)
        
        # Security
        self.secret_key = os.environ.get('SECRET_KEY', self.secret_key)
        cors_origins_str = os.environ.get('CORS_ORIGINS', '')
        if cors_origins_str:
            try:
                import json
                self.cors_origins = json.loads(cors_origins_str)
            except (json.JSONDecodeError, TypeError):
                # Fallback to comma-separated values
                self.cors_origins = [url.strip() for url in cors_origins_str.split(',') if url.strip()]
        
        # Feature Flags
        self.enable_agents = os.environ.get('ENABLE_AGENTS', str(self.enable_agents)).lower() in ['true', '1', 't']
        self.enable_research = os.environ.get('ENABLE_RESEARCH', str(self.enable_research)).lower() in ['true', '1', 't']
        self.enable_wiki = os.environ.get('ENABLE_WIKI', str(self.enable_wiki)).lower() in ['true', '1', 't']
        self.enable_simple = os.environ.get('ENABLE_SIMPLE', str(self.enable_simple)).lower() in ['true', '1', 't']
        self.enable_chat = os.environ.get('ENABLE_CHAT', str(self.enable_chat)).lower() in ['true', '1', 't']
        
        # Legacy Settings (Wiki authentication)
        raw_auth_mode = os.environ.get('GRANTHA_AUTH_MODE', str(self.wiki_auth_mode))
        self.wiki_auth_mode = raw_auth_mode.lower() in ['true', '1', 't']
        self.wiki_auth_code = os.environ.get('GRANTHA_AUTH_CODE', self.wiki_auth_code)
        
        # Configuration directory
        self.config_dir = os.environ.get('GRANTHA_CONFIG_DIR', self.config_dir)
        
        # Logging
        self.log_level = os.environ.get('LOG_LEVEL', self.log_level)
        self.log_format = os.environ.get('LOG_FORMAT', self.log_format)
        self.log_file = os.environ.get('LOG_FILE', self.log_file)
        
        # AI Model Configuration
        self.default_model = os.environ.get('DEFAULT_MODEL', self.default_model)
        self.default_temperature = float(os.environ.get('DEFAULT_TEMPERATURE', self.default_temperature))
        self.default_max_tokens = int(os.environ.get('DEFAULT_MAX_TOKENS', self.default_max_tokens))
        self.default_embedding_model = os.environ.get('DEFAULT_EMBEDDING_MODEL', self.default_embedding_model)
        
        # Build & Development
        self.debug = os.environ.get('DEBUG', str(self.debug)).lower() in ['true', '1', 't']
        self.build_version = os.environ.get('BUILD_VERSION', self.build_version)
        
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

# API Key constants for backward compatibility
OPENAI_API_KEY = _config.openai_api_key
GOOGLE_API_KEY = _config.google_api_key
OPENROUTER_API_KEY = _config.openrouter_api_key
AWS_ACCESS_KEY_ID = _config.aws_access_key_id
AWS_SECRET_ACCESS_KEY = _config.aws_secret_access_key
AWS_REGION = _config.aws_region
AWS_ROLE_ARN = _config.aws_role_arn
AZURE_OPENAI_API_KEY = _config.azure_openai_api_key
AZURE_OPENAI_ENDPOINT = _config.azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT = _config.azure_openai_deployment
DASHSCOPE_API_KEY = _config.dashscope_api_key


def get_model_config(provider: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Get model configuration for a specific provider and model.
    
    Args:
        provider: The provider name (e.g., "google", "openai", "openrouter")
        model: The model name (optional, will use default if not provided)
    
    Returns:
        Dictionary containing model configuration including model_client
    """
    generator_config = configs.get("generator", {})
    providers = generator_config.get("providers", {})
    
    if provider not in providers:
        raise ValueError(f"Provider '{provider}' not found in configuration")
    
    provider_config = providers[provider]
    
    # Use provided model or default
    if model is None:
        model = provider_config.get("default_model")
        if not model:
            raise ValueError(f"No default model configured for provider '{provider}'")
    
    models = provider_config.get("models", {})
    if model not in models:
        # For providers that support custom models, return basic config
        if provider_config.get("supportsCustomModel", False):
            model_config = {"temperature": 0.7}  # Default values
        else:
            raise ValueError(f"Model '{model}' not found for provider '{provider}'")
    else:
        model_config = models[model].copy()
    
    # Add provider-level information
    result = {
        "provider": provider,
        "model": model,
        "model_kwargs": model_config,
        "model_client": provider_config.get("model_client")
    }
    
    # If no model_client, try to get it from client mapping
    if not result["model_client"] and hasattr(_config_loader, 'client_classes'):
        client_class_name = provider_config.get("client_class")
        if client_class_name and client_class_name in _config_loader.client_classes:
            result["model_client"] = _config_loader.client_classes[client_class_name]
    
    return result


def reload_configs():
    """Reload all configurations."""
    global configs
    configs = {
        "generator": _config_loader.load_generator_config(),
        "embedder": _config_loader.load_embedder_config(), 
        "repo": _config_loader.load_repo_config(),
        "lang": _config_loader.load_lang_config()
    }