"""Database connection and management for MongoDB."""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
import certifi

# Configure logging
logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB connection manager."""
    
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

# Global MongoDB instance
mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection."""
    try:
        logger.info("Connecting to MongoDB...")
        ca = certifi.where()
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL, tlsCAFile=ca, ssl=True)
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        
        # Test the connection
        await mongodb.client.admin.command('ping')
        logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("Disconnected from MongoDB")

def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    return mongodb.database
