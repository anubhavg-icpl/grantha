"""API layer for the Grantha platform."""

from .app import create_app
from .routes import wiki_router, chat_router, research_router

__all__ = ["create_app", "wiki_router", "chat_router", "research_router"]