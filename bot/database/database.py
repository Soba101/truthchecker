"""
Database Connection and Initialization

This module handles database connection setup, initialization,
and provides the database session management.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData

from ..utils.config import get_settings
from ..utils.logging_config import get_logger

# Logger setup
logger = get_logger(__name__)

# Database metadata and base class
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Global database engine and session factory
engine = None
SessionLocal = None


async def init_database() -> None:
    """
    Initialize the database connection and create tables.
    
    This function sets up the async database engine and creates
    all necessary tables if they don't exist.
    """
    global engine, SessionLocal
    
    settings = get_settings()
    
    try:
        # Convert SQLite URL to async version if needed
        database_url = settings.database_url
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Create async engine
        engine = create_async_engine(
            database_url,
            echo=settings.debug,  # Log SQL queries in debug mode
            future=True
        )
        
        # Create session factory
        SessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Import all models to ensure they're registered with SQLAlchemy
        from .models import (
            # Core models
            User, Game, GamePlayer, TruthWarsGame, PlayerRole, Headline,
            
            # Refined system models for reputation tracking
            PlayerReputationHistory, HeadlineVote, RoundResult,
            
            # Shadow ban and snipe system models
            ShadowBanHistory, SnipeAction,
            
            # Educational and analytics models
            HeadlineUsage, MediaLiteracyAnalytics, DrunkRoleAssignment
        )
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"Database initialized successfully with refined Truth Wars schema - database_url: {database_url}")
        logger.info("Created tables for reputation system, Trust/Flag voting, shadow bans, and educational tracking")
        
    except Exception as e:
        logger.error(f"Failed to initialize database - error: {str(e)}")
        raise


async def get_db_session() -> AsyncSession:
    """
    Get a database session.
    
    Returns:
        AsyncSession: Database session for queries
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    return SessionLocal()


async def close_database() -> None:
    """
    Close the database connection.
    
    This should be called during application shutdown.
    """
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")


# Context manager for database sessions
class DatabaseSession:
    """
    Context manager for database sessions with automatic cleanup.
    
    Usage:
        async with DatabaseSession() as session:
            # Perform database operations
            result = await session.execute(query)
    """
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = await get_db_session()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is not None:
                await self.session.rollback()
            else:
                await self.session.commit()
            await self.session.close() 