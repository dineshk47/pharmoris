import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def init_db():
    try:
        async with engine.begin() as conn:
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logging.info("Vector extension created successfully")
            except Exception as e:
                logging.error(f"Failed to create vector extension: {str(e)}")
                raise
        
        # Verify the extension exists
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector';"))
            if not result.scalar():
                raise Exception("Vector extension not found after creation attempt")
            logging.info("Vector extension verified")
        
        # Then create the tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created")
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}")
        raise

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logging.info("Database connection successful! Result:", result.scalar())
    except Exception as e:
        logging.error("Database connection failed:", e)
