"""Migration script to update bookmark indexes from lecture_id/card_index to deck_id/flashcard_index."""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure
from dotenv import load_dotenv, find_dotenv
import certifi

# Load env from project root (backend/../.env)
load_dotenv(find_dotenv())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_bookmark_indexes():
    """Drop old bookmark indexes and create new ones with correct field names."""
    
    # Connect to MongoDB (reuse app config)
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "study_analytics")
    # Mirror backend/app/database.py TLS settings for Atlas compatibility
    ca = certifi.where()
    client = AsyncIOMotorClient(mongodb_url, tlsCAFile=ca, ssl=True)
    db = client[database_name]
    bookmarks_collection = db.bookmarks
    
    try:
        # Step 1: Drop the old unique index
        logger.info("Dropping old bookmark indexes...")
        try:
            await bookmarks_collection.drop_index("user_bookmark_unique")
            logger.info("✅ Dropped old 'user_bookmark_unique' index")
        except OperationFailure as e:
            if "index not found" in str(e).lower():
                logger.info("Old 'user_bookmark_unique' index doesn't exist, skipping")
            else:
                logger.warning(f"Error dropping old index: {e}")
        
        try:
            await bookmarks_collection.drop_index("course_lecture_bookmarks_index")
            logger.info("✅ Dropped old 'course_lecture_bookmarks_index' index")
        except OperationFailure as e:
            if "index not found" in str(e).lower():
                logger.info("Old 'course_lecture_bookmarks_index' index doesn't exist, skipping")
            else:
                logger.warning(f"Error dropping old index: {e}")
        
        # Step 2: Update existing documents to use new field names
        logger.info("Updating existing bookmark documents...")
        result = await bookmarks_collection.update_many(
            {"lecture_id": {"$exists": True}},
            [
                {
                    "$set": {
                        "deck_id": "$lecture_id",
                        "flashcard_index": "$card_index"
                    }
                },
                {
                    "$unset": ["lecture_id", "card_index"]
                }
            ]
        )
        logger.info(f"✅ Updated {result.modified_count} bookmark documents")
        
        # Step 3: Create new indexes with correct field names
        logger.info("Creating new bookmark indexes...")
        new_indexes = [
            IndexModel([("firebase_uid", ASCENDING)], name="firebase_uid_bookmarks_index"),
            IndexModel([("course_id", ASCENDING), ("deck_id", ASCENDING)], name="course_deck_bookmarks_index"),
            IndexModel([("created_at", ASCENDING)], name="bookmarks_created_at_index"),
            IndexModel([("firebase_uid", ASCENDING), ("course_id", ASCENDING), ("deck_id", ASCENDING), ("flashcard_index", ASCENDING)], 
                      unique=True, name="user_bookmark_unique")
        ]
        
        await bookmarks_collection.create_indexes(new_indexes)
        logger.info("✅ Created new bookmark indexes")
        
        logger.info("🎉 Bookmark index migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(migrate_bookmark_indexes())

