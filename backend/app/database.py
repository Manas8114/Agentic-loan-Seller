"""
Database Configuration and Session Management

Provides async SQLAlchemy engine and session factory for PostgreSQL.
Uses connection pooling for optimal performance.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def create_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.
    
    Returns:
        AsyncEngine: Configured async engine for PostgreSQL or SQLite.
    """
    is_sqlite = "sqlite" in settings.database_url
    
    # SQLite doesn't support pool_size/max_overflow
    if is_sqlite:
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            poolclass=NullPool,
        )
    else:
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )


# Global engine instance
engine = create_engine()

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.
    
    Yields:
        AsyncSession: Database session that auto-closes after use.
    
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Creates all tables defined in models if they don't exist.
    Should be called on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    await engine.dispose()
