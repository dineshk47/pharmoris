import pytest
import os
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import get_session
from app.core.config import get_settings
from app.documents.models import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/pharmoris_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def settings():
    """Override settings for testing"""
    # Set env file path for testing
    os.environ["ENV_FILE"] = os.path.join(
        os.path.dirname(__file__), ".env.test"
    )
    return get_settings()

@pytest.fixture(scope="session")
async def engine():
    """Create engine instance."""
    test_engine = create_async_engine(TEST_DATABASE_URL)
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield test_engine
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()

@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def override_get_session(db_session):
    """Override the get_session dependency for testing."""
    async def _get_session():
        yield db_session
    return _get_session