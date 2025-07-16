from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.engine import Engine
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import get_database_config
from ..models.database import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
engine = None
async_session_factory = None


async def init_database():
    """Initialize the database engine and create tables."""
    global engine, async_session_factory
    
    config = get_database_config()
    
    # Create async engine
    engine = create_async_engine(
        config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_timeout=config.pool_timeout,
    )
    
    # Create session factory
    async_session_factory = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def close_database():
    """Close the database connection."""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session with proper cleanup."""
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with get_db_session() as session:
        yield session