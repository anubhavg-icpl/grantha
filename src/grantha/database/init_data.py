"""Database initialization with default data."""

import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .connection import async_session
from .services import UserService
from .models import User

logger = logging.getLogger(__name__)


async def create_default_admin_user():
    """Create a default admin user if none exists."""
    async with async_session() as session:
        try:
            # Check if any superuser exists
            result = await session.execute(
                select(User).where(User.is_superuser == True).limit(1)
            )
            existing_admin = result.scalar_one_or_none()
            if existing_admin:
                logger.info("Admin user already exists, skipping creation")
                return
            
            # Create default admin user
            admin_user = await UserService.create_user(
                session=session,
                username="admin",
                password="grantha123",  # Change this in production!
                email="admin@grantha.dev",
                full_name="Grantha Administrator",
                is_verified=True,
                is_superuser=True
            )
            
            logger.info(f"Created default admin user: {admin_user.username}")
            logger.warning("Default admin password is 'grantha123' - please change it immediately!")
            
        except Exception as e:
            logger.error(f"Failed to create default admin user: {e}")


async def initialize_default_data():
    """Initialize database with default data."""
    logger.info("Initializing database with default data...")
    
    try:
        await create_default_admin_user()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


if __name__ == "__main__":
    asyncio.run(initialize_default_data())