# 📚 Grantha - AI-Powered Knowledge Management Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-2.0+-orange.svg)](https://kit.svelte.dev/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Grantha (ग्रंथ) is a comprehensive AI-powered knowledge management and documentation platform that supports multiple LLM providers, implements RAG (Retrieval Augmented Generation), and offers advanced research capabilities with a modern web interface.

## ✨ Features

### Backend (Python/FastAPI)
- **🤖 Multi-Provider AI Support**: Seamlessly integrate with OpenAI, Google Gemini, Azure, AWS Bedrock, and more
- **📖 RAG Implementation**: Advanced retrieval-augmented generation for context-aware responses
- **🔬 Deep Research**: Multi-round research capabilities with comprehensive analysis
- **📝 Wiki Generation**: Automatic documentation generation with Mermaid diagrams
- **🔄 Real-time Processing**: WebSocket support for streaming responses
- **🎯 Embeddings**: Multiple embedding providers for semantic search
- **🏗️ Clean Architecture**: Professional project structure with separation of concerns

### Frontend (SvelteKit)
- **🎨 Modern UI**: Responsive design with shadcn-ui components and Tailwind CSS
- **💬 Real-time Chat**: WebSocket-powered streaming chat interface
- **⚙️ Model Management**: Dynamic AI model configuration and provider selection
- **📚 Wiki Interface**: Documentation generation and browsing capabilities
- **🤝 Agent Coordination**: UI for managing 20+ specialized AI agents
- **🔒 Authentication**: Secure API key validation with persistent sessions
- **🌓 Dark/Light Mode**: System-aware theme switching with accessibility support

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- Node.js 18+ and npm/pnpm/yarn
- Virtual environment (recommended)
- API keys for at least one provider (OpenAI, Google, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/anubhavg-icpl/grantha.git
cd grantha

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd frontend
npm install
cd ..
```

### Running the Application

```bash
# Terminal 1: Start the backend API
python main.py

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

**Access the application:**
- 🖥️ **Web Interface**: `http://localhost:5173`
- 📖 **API Docs**: `http://localhost:8000/docs`
- 📊 **Alternative API Docs**: `http://localhost:8000/redoc`

## 📁 Project Structure

```
grantha/
├── src/grantha/           # Backend: Main application package
│   ├── api/              # FastAPI application and routes
│   ├── clients/          # AI provider client implementations
│   ├── core/             # Core configuration and logging
│   ├── models/           # Pydantic data models
│   └── utils/            # Utility modules (RAG, research, etc.)
├── frontend/              # Frontend: SvelteKit application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/ # Reusable UI components
│   │   │   ├── api/       # API client and WebSocket
│   │   │   ├── stores/    # Svelte stores for state management
│   │   │   ├── types/     # TypeScript type definitions
│   │   │   └── utils/     # Utility functions
│   │   ├── routes/        # SvelteKit routes and pages
│   │   └── app.html       # HTML template
│   ├── static/           # Static assets
│   └── package.json      # Frontend dependencies
├── tests/                # Test suites
├── docs/                 # Documentation
├── configs/              # Configuration files
├── .claude/              # Claude agent configurations
│   └── agents/          # 20+ specialized AI agents
└── .github/              # GitHub Actions workflows
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

# Authentication (optional)
WIKI_AUTH_MODE=false
WIKI_AUTH_CODE=your_secret_code
```

### Configuration Files

- `configs/generator.json` - LLM generation settings
- `configs/embedder.json` - Embedding model configuration
- `configs/repo.json` - Repository and data settings
- `configs/lang.json` - Language detection settings

## 🎯 Core Features

### 1. Web Interface
Access all features through the modern web interface:
- **Dashboard**: Overview of system status and quick actions
- **Chat**: Real-time conversations with AI models
- **Wiki**: Generate and browse documentation
- **Research**: Deep research and analysis tools
- **Models**: Configure AI providers and models
- **Agents**: Coordinate specialized AI agents

### 2. API Endpoints

#### Simple Chat
```python
import requests

response = requests.post(
    "http://localhost:8000/simple/chat",
    json={"user_query": "What is machine learning?", "provider": "openai"}
)
print(response.json()["response"])
```

#### RAG (Retrieval Augmented Generation)
```python
response = requests.post(
    "http://localhost:8000/simple/rag",
    json={
        "query": "How does the authentication work?",
        "repo_url": "https://github.com/user/repo",
        "k": 5
    }
)
```

#### Deep Research
```python
response = requests.post(
    "http://localhost:8000/research/deep",
    json={
        "query": "Latest advances in RAG systems",
        "repo_url": "https://github.com/user/repo",
        "provider": "openai"
    }
)
```

#### Wiki Generation
```python
response = requests.post(
    "http://localhost:8000/wiki/generate",
    json={
        "repo_url": "https://github.com/user/repo",
        "language": "en",
        "provider": "google"
    }
)
```

## 🤖 Specialized AI Agents

Grantha includes 20+ specialized agents for different development tasks:

- **fullstack-developer**: Complete feature implementation
- **api-designer**: REST/GraphQL API design
- **websocket-engineer**: Real-time features
- **typescript-pro**: Type safety and best practices
- **ai-engineer**: LLM integration and ML pipelines
- **security-auditor**: Vulnerability assessment
- **documentation-engineer**: Technical documentation
- And many more...

## 🧪 Testing

```bash
# Backend tests
pytest
pytest --cov=src/grantha --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:coverage

# Run specific test categories
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m e2e         # End-to-end tests only

# Using Make commands
make test           # Run unit tests
make test-all       # Run all tests with coverage
make test-fast      # Quick smoke tests
```

## 🚢 Deployment

### Docker Compose (Recommended)

```bash
# Build and run both backend and frontend
docker-compose up -d

# View logs
docker-compose logs -f
```

### Individual Deployment

#### Backend
```bash
# Build backend image
docker build -t grantha-api .
docker run -p 8000:8000 --env-file .env grantha-api
```

#### Frontend
```bash
# Build frontend
cd frontend
npm run build

# Serve static files or deploy to CDN
npm run preview
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
- [Frontend Documentation](frontend/README.md) - Frontend-specific documentation
- [Agent Configuration](docs/AGENTS.md) - AI agent setup and customization

## 🛠️ Development

### Backend Development
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
```

### Frontend Development
```bash
cd frontend

# Development server with hot reload
npm run dev

# Type checking
npm run check
npm run check:watch

# Linting and formatting
npm run lint
npm run format
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
- CSRF protection
- XSS prevention

## 📈 Performance

- Async/await for concurrent processing
- Connection pooling for database operations
- Caching for frequently accessed data
- Optimized embedding storage with FAISS
- Streaming responses for large outputs
- Code splitting and lazy loading in frontend
- Optimized bundle sizes

## 🐛 Troubleshooting

Common issues and solutions:

### Backend Issues
1. **Import errors**: Ensure you're in the virtual environment
2. **API key errors**: Check your `.env` file has valid keys
3. **Port conflicts**: Change the PORT in `.env`
4. **Memory issues**: Adjust batch sizes in configs

### Frontend Issues
1. **Build errors**: Clear node_modules and reinstall
2. **API connection**: Check backend is running on correct port
3. **WebSocket issues**: Verify WebSocket endpoint configuration

For more help, see [troubleshooting guide](docs/TROUBLESHOOTING.md) or open an issue.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Backend
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI capabilities powered by multiple LLM providers
- Embedding search with [FAISS](https://github.com/facebookresearch/faiss)
- Testing with [pytest](https://pytest.org/)

### Frontend
- Built with [SvelteKit](https://kit.svelte.dev/)
- UI components inspired by [shadcn-ui](https://ui.shadcn.com/)
- Styling with [Tailwind CSS](https://tailwindcss.com/)
- Icons by [Lucide](https://lucide.dev/)

## 📬 Contact

- GitHub Issues: [github.com/anubhavg-icpl/grantha/issues](https://github.com/anubhavg-icpl/grantha/issues)
- Email: support@grantha.ai
- Documentation: [docs.grantha.ai](https://docs.grantha.ai)

---

<p align="center">Made with ❤️ by the Grantha Team</p>