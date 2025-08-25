# ग्रंथ (Grantha) API

AI-powered knowledge management and documentation API, configured with Google Gemini API.

## ✅ Setup Complete

The Grantha API is now running independently as a knowledge management system.

## Project Structure

```
grantha/
├── api/                  # Backend API server
│   ├── main.py          # API entry point
│   ├── api.py           # FastAPI implementation
│   ├── config.py        # Configuration management
│   ├── config/          # JSON configuration files
│   └── ...              # Other API modules
├── venv/                # Python virtual environment
├── .env                 # Environment variables (API keys)
└── test_api.py         # Test script
```

## Configuration

Your API keys are configured in `.env`:
- `GOOGLE_API_KEY` - For Google Gemini text generation
- `OPENAI_API_KEY` - Placeholder for embeddings (optional)

## Running the Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start the API server
python -m api.main
```

The server will run on http://localhost:8001

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /api/wiki/generate` - Generate wiki documentation
- `POST /api/chat/stream` - Streaming chat completions
- More endpoints available in `api/api.py`

## Testing

```bash
# Run the test script
source venv/bin/activate
python test_api.py
```

## Dependencies

All Python dependencies are installed in the virtual environment:
- FastAPI & Uvicorn for the web server
- Google Generative AI for text generation
- Various other packages for embeddings and processing

## Notes

- The backend is currently running on port 8001
- Google Gemini is configured as the default text generation model
- For full embedding functionality, replace the placeholder OpenAI key with a real one