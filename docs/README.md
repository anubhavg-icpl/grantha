# ग्रंथ (Grantha) API Documentation

## Overview

Grantha is an AI-powered knowledge management and documentation system that provides intelligent wiki generation, deep research capabilities, and multi-provider LLM integration. The system supports multiple AI providers including Google Gemini, OpenAI, OpenRouter, Ollama, AWS Bedrock, Azure AI, and DashScope.

## Quick Links

- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Development Setup](DEVELOPMENT.md)
- [Contributing Guide](CONTRIBUTING.md)

## Key Features

- **Multi-Provider LLM Support**: Seamless integration with multiple AI providers
- **Intelligent Wiki Generation**: Automated documentation generation from codebases
- **Deep Research Capabilities**: Advanced research and analysis tools
- **WebSocket Support**: Real-time streaming for chat and research operations
- **RAG (Retrieval-Augmented Generation)**: Context-aware responses using embeddings
- **Flexible Configuration**: JSON-based configuration for models and providers
- **Multi-language Support**: Support for 10+ languages including English, Japanese, Chinese, Spanish, and more

## Core Components

### API Server (`api/`)
- **FastAPI-based REST API** with WebSocket support
- **Multi-provider client architecture** for different AI services
- **Caching system** for wiki structures and research data
- **Authentication and authorization** system

### Wiki System
- **Automated wiki generation** from repository analysis
- **Structured content organization** with sections and subsections
- **Export capabilities** in Markdown and JSON formats
- **Real-time generation progress** via WebSocket streams

### Research Engine
- **Deep research capabilities** with multi-step analysis
- **Context-aware information retrieval**
- **Streaming research results** for real-time updates

## Supported AI Providers

| Provider | Models | Features |
|----------|---------|----------|
| Google Gemini | gemini-1.5-pro, gemini-1.5-flash | Chat, embeddings, function calling |
| OpenAI | gpt-4, gpt-3.5-turbo, text-embedding-3-small | Chat, embeddings, function calling |
| OpenRouter | Various models | Unified API for multiple providers |
| Ollama | Local models | Self-hosted AI models |
| AWS Bedrock | Claude, Llama, Titan | Enterprise AI services |
| Azure AI | GPT models via Azure | Microsoft cloud AI |
| DashScope | Qwen models | Alibaba cloud AI |

## Getting Started

1. **Installation**
   ```bash
   git clone https://github.com/anubhavg-icpl/grantha.git
   cd grantha
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the API**
   ```bash
   python -m api.main
   ```

4. **Access the API**
   - Health check: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `OPENROUTER_API_KEY` | OpenRouter API key | Optional |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock | Optional |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for Bedrock | Optional |
| `AWS_REGION` | AWS region for Bedrock | Optional |
| `GRANTHA_AUTH_MODE` | Enable authentication (true/false) | Optional |
| `GRANTHA_AUTH_CODE` | Authentication code | Optional |
| `GRANTHA_CONFIG_DIR` | Custom configuration directory | Optional |

## Configuration Files

The system uses JSON configuration files located in `api/config/`:

- `generator.json` - LLM provider and model configurations
- `embedder.json` - Embedding model configurations
- `repo.json` - Repository analysis and filtering settings
- `lang.json` - Supported languages configuration

## API Endpoints Overview

### Core Endpoints
- `GET /health` - System health check
- `GET /` - API welcome message
- `GET /models/config` - Available models and providers

### Wiki Operations
- `POST /api/wiki/generate` - Generate wiki structure from repository
- `GET /api/wiki_cache` - Retrieve cached wiki data
- `POST /api/wiki_cache` - Store wiki cache
- `DELETE /api/wiki_cache` - Clear wiki cache
- `POST /export/wiki` - Export wiki in various formats

### Research Operations
- `POST /api/research/deep` - Conduct deep research with streaming
- `POST /chat/completions/stream` - Chat completions with streaming

### Repository Operations
- `GET /local_repo/structure` - Analyze local repository structure
- `GET /api/processed_projects` - List processed projects

For detailed API documentation, see [API_REFERENCE.md](API_REFERENCE.md).

## Architecture

Grantha follows a modular architecture with clear separation of concerns:

- **API Layer**: FastAPI-based REST API with WebSocket support
- **Service Layer**: Business logic for wiki generation, research, and chat
- **Client Layer**: Abstracted AI provider clients
- **Configuration Layer**: JSON-based configuration management
- **Cache Layer**: Intelligent caching for performance optimization

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Development

To contribute to Grantha, please see our [CONTRIBUTING.md](CONTRIBUTING.md) guide and [DEVELOPMENT.md](DEVELOPMENT.md) setup instructions.

## License

[Add your license information here]

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API reference

---

*Last updated: 2025-08-25*
