import asyncio
import logging
from app.db.initdb import test_connection

asyncio.run(test_connection())


import asyncio
from app.db.initdb import engine, Base

async def recreate_tables():
    async with engine.begin() as conn:
        print("Dropping all existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Recreating tables...")
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Tables recreated successfully!")

asyncio.run(recreate_tables())
