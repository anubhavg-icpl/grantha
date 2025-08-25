#!/usr/bin/env python3
"""Main entry point for the Grantha API server."""

import uvicorn
import os
import sys
import logging
from dotenv import load_dotenv

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables from .env file
load_dotenv()

from src.grantha.core.logging_config import setup_logging
from src.grantha.api.app import create_app

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Check for required environment variables
required_env_vars = ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
    logger.warning("Some functionality may not work correctly without these variables.")

# Configure Google Generative AI
import google.generativeai as genai
from src.grantha.core.config import get_config

config = get_config()
if config.google_api_key:
    genai.configure(api_key=config.google_api_key)
else:
    logger.warning("GOOGLE_API_KEY not configured")


def main():
    """Main entry point."""
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8001))

    # Create the FastAPI app
    app = create_app()

    logger.info(f"🚀 Starting ग्रंथ (Grantha) API on port {port}")

    # Run the FastAPI app with uvicorn
    # Disable reload in production/Docker environment
    is_development = os.environ.get("NODE_ENV") != "production"
    
    if is_development:
        # Prevent infinite logging loop caused by file changes triggering log writes
        logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

    if is_development:
        uvicorn.run(
            "main:create_app",
            host="0.0.0.0",
            port=port,
            reload=True,
            factory=True
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False
        )


if __name__ == "__main__":
    main()