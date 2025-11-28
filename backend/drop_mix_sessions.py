import asyncio
import logging
from app.db.postgres import init_postgres_db, get_postgres_pool, close_postgres_db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def drop_table():
    try:
        # Initialize DB
        await init_postgres_db()
        pool = await get_postgres_pool()
        
        logger.info("Dropping mix_sessions table...")
        async with pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS mix_sessions CASCADE;")
        logger.info("Table dropped successfully. Restart the backend to recreate it with new schema.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_postgres_db()

if __name__ == "__main__":
    asyncio.run(drop_table())

