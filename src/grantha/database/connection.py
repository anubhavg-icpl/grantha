"""Database connection and session management for Grantha."""

import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

from .base import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./grantha.db"  # Default to SQLite for development
)

# Parse database URL to determine dialect
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
    )
else:
    # Generic configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    )

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    This is designed to be used with FastAPI's dependency injection system.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize the database by creating all tables."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from . import models  # noqa: F401
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_database():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Database health check
async def check_database_health() -> bool:
    """Check database connectivity."""
    try:
        async with async_session() as session:
            # Simple query to test connection
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False