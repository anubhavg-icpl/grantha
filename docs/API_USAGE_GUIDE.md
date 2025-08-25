# Grantha API Usage Guide

## Table of Contents
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Advanced Features](#advanced-features)
- [Code Examples](#code-examples)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/anubhavg-icpl/grantha.git
cd grantha

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the API

```bash
# Development mode
python main.py

# Production mode
NODE_ENV=production python main.py

# Using Docker
docker-compose up
```

The API will be available at `http://localhost:8001`

## Authentication

### API Keys Required

Set these environment variables in your `.env` file:

```env
# Required for core functionality
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional providers
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
DASHSCOPE_API_KEY=your_dashscope_key
OPENROUTER_API_KEY=your_openrouter_key
```

## Core Endpoints

### 1. Chat Completion
Generate AI responses using various providers.

**Endpoint:** `POST /v1/chat`

**Request:**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "I'm doing well, thank you! How can I help you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  }
}
```

### 2. Simple Chat
Simplified chat interface for quick interactions.

**Endpoint:** `POST /simple_chat`

**Request:**
```json
{
  "query": "What is the capital of France?",
  "provider": "openai",
  "stream": false
}
```

### 3. RAG (Retrieval Augmented Generation)
Query with context from your knowledge base.

**Endpoint:** `POST /rag`

**Request:**
```json
{
  "query": "What are the main features of Grantha?",
  "repo_id": "grantha-docs",
  "top_k": 5,
  "provider": "openai"
}
```

### 4. Deep Research
Conduct comprehensive research on topics.

**Endpoint:** `POST /deep_research`

**Request:**
```json
{
  "topic": "Latest advances in RAG systems",
  "max_rounds": 3,
  "max_depth": 2,
  "provider": "openai"
}
```

**Response:**
```json
{
  "research": {
    "summary": "Comprehensive research summary...",
    "key_findings": ["Finding 1", "Finding 2"],
    "sources": ["Source 1", "Source 2"],
    "confidence": 0.85
  },
  "rounds_completed": 3,
  "tokens_used": 5000
}
```

### 5. Wiki Generation
Generate comprehensive wiki-style documentation.

**Endpoint:** `POST /wiki`

**Request:**
```json
{
  "topic": "Machine Learning Fundamentals",
  "sections": ["introduction", "concepts", "applications"],
  "depth": "comprehensive",
  "provider": "openai"
}
```

### 6. WebSocket Wiki Generation
Real-time wiki generation with progress updates.

**Endpoint:** `WS /ws/wiki`

**WebSocket Message:**
```json
{
  "topic": "Quantum Computing",
  "stream": true
}
```

## Advanced Features

### Streaming Responses

Enable streaming for real-time token generation:

```python
import requests
import json

response = requests.post(
    "http://localhost:8001/v1/chat",
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Write a story"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        print(data['choices'][0]['delta']['content'], end='')
```

### Provider Selection

Choose from multiple AI providers:

- **OpenAI**: GPT-4, GPT-3.5
- **Google**: Gemini Pro, Gemini Ultra
- **Azure**: Azure OpenAI deployments
- **AWS Bedrock**: Claude, Llama
- **Dashscope**: Qwen models
- **OpenRouter**: Access to 100+ models

```python
# Use different providers
providers = ["openai", "google", "azure", "bedrock", "dashscope", "openrouter"]

for provider in providers:
    response = requests.post(
        "http://localhost:8001/simple_chat",
        json={
            "query": "Hello",
            "provider": provider
        }
    )
    print(f"{provider}: {response.json()['response']}")
```

## Code Examples

### Python Client

```python
import requests
import json

class GranthaClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url

    def chat(self, message, provider="openai"):
        """Send a chat message."""
        response = requests.post(
            f"{self.base_url}/simple_chat",
            json={"query": message, "provider": provider}
        )
        return response.json()["response"]

    def research(self, topic):
        """Conduct deep research."""
        response = requests.post(
            f"{self.base_url}/deep_research",
            json={"topic": topic, "max_rounds": 3}
        )
        return response.json()

    def rag_query(self, query, repo_id):
        """Query with RAG."""
        response = requests.post(
            f"{self.base_url}/rag",
            json={"query": query, "repo_id": repo_id}
        )
        return response.json()

# Usage
client = GranthaClient()
response = client.chat("What is machine learning?")
print(response)
```

### JavaScript/TypeScript Client

```typescript
class GranthaClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://localhost:8001") {
    this.baseUrl = baseUrl;
  }

  async chat(message: string, provider: string = "openai"): Promise<string> {
    const response = await fetch(`${this.baseUrl}/simple_chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: message, provider })
    });
    const data = await response.json();
    return data.response;
  }

  async streamChat(message: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: "gpt-4",
        messages: [{ role: "user", content: message }],
        stream: true
      })
    });

    const reader = response.body?.getReader();
    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = new TextDecoder().decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          process.stdout.write(data.choices[0].delta.content || '');
        }
      }
    }
  }
}

// Usage
const client = new GranthaClient();
await client.chat("Hello, Grantha!");
```

### cURL Examples

```bash
# Simple chat
curl -X POST http://localhost:8001/simple_chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "provider": "openai"}'

# Deep research
curl -X POST http://localhost:8001/deep_research \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI Safety", "max_rounds": 3}'

# RAG query
curl -X POST http://localhost:8001/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "How does RAG work?", "repo_id": "docs"}'

# Streaming chat
curl -X POST http://localhost:8001/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Tell me a joke"}], "stream": true}' \
  --no-buffer
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error Response Format:
```json
{
  "error": {
    "message": "Invalid model specified",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

### Error Handling Example

```python
def safe_api_call(endpoint, payload):
    try:
        response = requests.post(
            f"http://localhost:8001/{endpoint}",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limited. Waiting...")
            time.sleep(60)
            return safe_api_call(endpoint, payload)
        elif e.response.status_code == 400:
            print(f"Bad request: {e.response.json()['error']['message']}")
        else:
            print(f"HTTP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None
```

## Rate Limiting

Default rate limits:
- **Simple Chat**: 100 requests/minute
- **Deep Research**: 10 requests/minute
- **Wiki Generation**: 5 requests/minute
- **RAG Queries**: 50 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1677652288
```

## Best Practices

### 1. Use Environment Variables
Never hardcode API keys in your code:

```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

### 2. Implement Retry Logic
Handle transient failures gracefully:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_api(endpoint, data):
    response = requests.post(endpoint, json=data)
    response.raise_for_status()
    return response.json()
```

### 3. Cache Responses
Reduce API calls for repeated queries:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_chat(message_hash):
    return client.chat(message)

# Use hash for cache key
message = "What is AI?"
message_hash = hashlib.md5(message.encode()).hexdigest()
response = cached_chat(message_hash)
```

### 4. Monitor Usage
Track token usage and costs:

```python
def track_usage(response):
    usage = response.get("usage", {})
    tokens = usage.get("total_tokens", 0)
    cost = calculate_cost(tokens, model="gpt-4")
    log_metrics(tokens=tokens, cost=cost)
    return response
```

## WebSocket Usage

For real-time wiki generation:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/wiki');

ws.onopen = () => {
  ws.send(JSON.stringify({
    topic: "Machine Learning",
    stream: true
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress') {
    console.log(`Progress: ${data.progress}%`);
  } else if (data.type === 'section') {
    console.log(`New section: ${data.title}`);
    console.log(data.content);
  } else if (data.type === 'complete') {
    console.log('Wiki generation complete!');
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  grantha:
    build: .
    ports:
      - "8001:8001"
    environment:
      - NODE_ENV=production
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./configs:/app/configs
      - ./logs:/app/logs
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Health Check

Monitor API health:

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": {
    "openai": "active",
    "google": "active",
    "azure": "inactive"
  },
  "uptime": 3600
}
```

## Support

- **Documentation**: [/docs](http://localhost:8001/docs)
- **API Reference**: [/redoc](http://localhost:8001/redoc)
- **GitHub Issues**: [github.com/anubhavg-icpl/grantha/issues](https://github.com/anubhavg-icpl/grantha/issues)
- **Email**: support@grantha.ai

## License

MIT License - See LICENSE file for details.
