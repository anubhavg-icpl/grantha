# 📚 Grantha - AI-Powered Knowledge Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Grantha (ग्रंथ) is a comprehensive AI-powered knowledge management and documentation platform that supports multiple LLM providers, implements RAG (Retrieval Augmented Generation), and offers advanced research capabilities.

## ✨ Features

- **🤖 Multi-Provider AI Support**: Seamlessly integrate with OpenAI, Google Gemini, Azure, AWS Bedrock, and more
- **📖 RAG Implementation**: Advanced retrieval-augmented generation for context-aware responses
- **🔬 Deep Research**: Multi-round research capabilities with comprehensive analysis
- **📝 Wiki Generation**: Automatic documentation generation with Mermaid diagrams
- **🔄 Real-time Processing**: WebSocket support for streaming responses
- **🎯 Embeddings**: Multiple embedding providers for semantic search
- **🏗️ Clean Architecture**: Professional project structure with separation of concerns
- **🧪 Comprehensive Testing**: Unit, integration, and performance test suites
- **🚀 Production Ready**: Docker support, CI/CD pipelines, and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Virtual environment (recommended)
- API keys for at least one provider (OpenAI, Google, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/anubhavg-icpl/grantha.git
cd grantha

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the API

```bash
# Development mode with auto-reload
python main.py

# Production mode
NODE_ENV=production python main.py
```

The API will be available at `http://localhost:8001`

- 📖 Interactive API docs: `http://localhost:8001/docs`
- 📊 Alternative API docs: `http://localhost:8001/redoc`

## 📁 Project Structure

```
grantha/
├── src/grantha/           # Main application package
│   ├── api/              # FastAPI application and routes
│   ├── clients/          # AI provider client implementations
│   ├── core/             # Core configuration and logging
│   ├── models/           # Pydantic data models
│   └── utils/            # Utility modules (RAG, research, etc.)
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                 # Documentation
├── configs/              # Configuration files
├── .github/              # GitHub Actions workflows
└── scripts/              # Development and deployment scripts
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your API keys:

```env
# Required
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional providers
AZURE_OPENAI_API_KEY=your_azure_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
DASHSCOPE_API_KEY=your_dashscope_key
OPENROUTER_API_KEY=your_openrouter_key
```

### Configuration Files

- `configs/generator.json` - LLM generation settings
- `configs/embedder.json` - Embedding model configuration
- `configs/repo.json` - Repository and data settings
- `configs/lang.json` - Language detection settings

## 🎯 Core Features

### 1. Simple Chat
Quick AI responses with provider selection:

```python
import requests

response = requests.post(
    "http://localhost:8001/simple_chat",
    json={"query": "What is machine learning?", "provider": "openai"}
)
print(response.json()["response"])
```

### 2. RAG (Retrieval Augmented Generation)
Context-aware responses using your knowledge base:

```python
response = requests.post(
    "http://localhost:8001/rag",
    json={
        "query": "How does the authentication work?",
        "repo_id": "docs",
        "top_k": 5
    }
)
```

### 3. Deep Research
Comprehensive multi-round research on topics:

```python
response = requests.post(
    "http://localhost:8001/deep_research",
    json={
        "topic": "Latest advances in RAG systems",
        "max_rounds": 3,
        "provider": "openai"
    }
)
```

### 4. Wiki Generation
Generate comprehensive documentation:

```python
response = requests.post(
    "http://localhost:8001/wiki",
    json={
        "topic": "Machine Learning Fundamentals",
        "sections": ["introduction", "concepts", "applications"],
        "provider": "google"
    }
)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/grantha --cov-report=html

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m e2e        # End-to-end tests only

# Using Make commands
make test           # Run unit tests
make test-all       # Run all tests with coverage
make test-fast      # Quick smoke tests
```

## 🚢 Deployment

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Build image manually
docker build -t grantha:latest .
docker run -p 8001:8001 --env-file .env grantha:latest
```

### Production Deployment

1. Set environment variables for production
2. Configure reverse proxy (nginx/Apache)
3. Set up SSL certificates
4. Configure monitoring and logging
5. Set up database backups

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📖 Documentation

- [API Usage Guide](docs/API_USAGE_GUIDE.md) - Complete API reference with examples
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Development Guide](docs/DEVELOPMENT.md) - Setup and development workflow
- [API Reference](docs/API_REFERENCE.md) - Detailed endpoint documentation

## 🛠️ Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/
isort src/ tests/

# Run linting
flake8 src/ tests/
mypy src/

# Run security checks
bandit -r src/
safety check
```

## 📊 Supported Providers

| Provider | Models | Status | Features |
|----------|--------|--------|----------|
| OpenAI | GPT-4, GPT-3.5 | ✅ Active | Chat, Embeddings, Streaming |
| Google | Gemini Pro/Ultra | ✅ Active | Chat, Embeddings, Vision |
| Azure OpenAI | GPT-4, GPT-3.5 | ✅ Active | Chat, Embeddings, Streaming |
| AWS Bedrock | Claude, Llama | ✅ Active | Chat, Streaming |
| Dashscope | Qwen | ✅ Active | Chat, Embeddings |
| OpenRouter | 100+ models | ✅ Active | Chat, Routing |
| Ollama | Local models | ✅ Active | Chat, Embeddings, Offline |

## 🔒 Security

- API key management via environment variables
- Request validation with Pydantic
- Rate limiting and throttling
- Input sanitization
- Secure error handling

## 📈 Performance

- Async/await for concurrent processing
- Connection pooling for database operations
- Caching for frequently accessed data
- Optimized embedding storage with FAISS
- Streaming responses for large outputs

## 🐛 Troubleshooting

Common issues and solutions:

1. **Import errors**: Ensure you're in the virtual environment
2. **API key errors**: Check your `.env` file has valid keys
3. **Port conflicts**: Change the PORT in `.env`
4. **Memory issues**: Adjust batch sizes in configs

For more help, see [troubleshooting guide](docs/TROUBLESHOOTING.md) or open an issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI capabilities powered by multiple LLM providers
- Embedding search with [FAISS](https://github.com/facebookresearch/faiss)
- Testing with [pytest](https://pytest.org/)

## 📬 Contact

- GitHub Issues: [github.com/anubhavg-icpl/grantha/issues](https://github.com/anubhavg-icpl/grantha/issues)
- Email: support@grantha.ai
- Documentation: [docs.grantha.ai](https://docs.grantha.ai)

---

<p align="center">Made with ❤️ by the Grantha Team</p>
