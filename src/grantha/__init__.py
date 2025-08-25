"""
Grantha - AI-powered knowledge management and documentation platform.

This package provides a comprehensive suite of tools for:
- Multi-provider AI client management
- Document processing and embedding
- RAG (Retrieval-Augmented Generation) capabilities
- Wiki generation and management
- Deep research functionality
"""

from .core.config import Config
from .api.app import create_app

__version__ = "0.1.0"
__all__ = ["Config", "create_app"]