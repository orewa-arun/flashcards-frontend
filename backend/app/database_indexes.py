"""Database indexes for optimal performance and data integrity."""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

async def create_indexes(db: AsyncIOMotorDatabase):
    """
    Create database indexes for optimal performance and data integrity.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Users collection indexes
        users_collection = db.users
        user_indexes = [
            IndexModel([("firebase_uid", ASCENDING)], unique=True, name="firebase_uid_unique"),
            IndexModel([("email", ASCENDING)], sparse=True, name="email_index"),
            IndexModel([("created_at", ASCENDING)], name="created_at_index"),
            IndexModel([("last_active", ASCENDING)], name="last_active_index")
        ]
        
        try:
            await users_collection.create_indexes(user_indexes)
            logger.info("✅ Created indexes for users collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("Users collection indexes already exist")
            else:
                logger.error(f"Error creating users indexes: {e}")
        
        # User deck performance collection indexes
        performance_collection = db.user_deck_performance
        performance_indexes = [
            IndexModel([("firebase_uid", ASCENDING), ("course_id", ASCENDING), ("deck_id", ASCENDING)], 
                      unique=True, name="user_course_deck_unique"),
            IndexModel([("firebase_uid", ASCENDING)], name="firebase_uid_performance_index"),
            IndexModel([("course_id", ASCENDING)], name="course_id_index"),
            IndexModel([("last_quiz_date", ASCENDING)], name="last_quiz_date_index"),
            IndexModel([("updated_at", ASCENDING)], name="performance_updated_at_index")
        ]
        
        try:
            await performance_collection.create_indexes(performance_indexes)
            logger.info("✅ Created indexes for user_deck_performance collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("User deck performance collection indexes already exist")
            else:
                logger.error(f"Error creating performance indexes: {e}")
        
        # Quiz sessions collection indexes
        sessions_collection = db.quiz_sessions
        session_indexes = [
            IndexModel([("quiz_id", ASCENDING)], unique=True, name="quiz_id_unique"),
            IndexModel([("firebase_uid", ASCENDING)], name="firebase_uid_sessions_index"),
            IndexModel([("course_id", ASCENDING), ("deck_id", ASCENDING)], name="course_deck_sessions_index"),
            IndexModel([("created_at", ASCENDING)], name="sessions_created_at_index"),
            IndexModel([("completed", ASCENDING)], name="completed_index")
        ]
        
        try:
            await sessions_collection.create_indexes(session_indexes)
            logger.info("✅ Created indexes for quiz_sessions collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("Quiz sessions collection indexes already exist")
            else:
                logger.error(f"Error creating session indexes: {e}")
        
        # Quiz results collection indexes
        results_collection = db.quiz_results
        results_indexes = [
            IndexModel([("firebase_uid", ASCENDING)], name="firebase_uid_results_index"),
            IndexModel([("course_id", ASCENDING), ("deck_id", ASCENDING)], name="course_deck_results_index"),
            IndexModel([("quiz_id", ASCENDING)], name="quiz_id_results_index"),
            IndexModel([("completed_at", ASCENDING)], name="results_completed_at_index"),
            IndexModel([("firebase_uid", ASCENDING), ("completed_at", ASCENDING)], name="user_history_index")
        ]
        
        try:
            await results_collection.create_indexes(results_indexes)
            logger.info("✅ Created indexes for quiz_results collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("Quiz results collection indexes already exist")
            else:
                logger.error(f"Error creating results indexes: {e}")
        
        # Bookmarks collection indexes (if exists)
        bookmarks_collection = db.bookmarks
        bookmark_indexes = [
            IndexModel([("firebase_uid", ASCENDING)], name="firebase_uid_bookmarks_index"),
            IndexModel([("course_id", ASCENDING), ("lecture_id", ASCENDING)], name="course_lecture_bookmarks_index"),
            IndexModel([("created_at", ASCENDING)], name="bookmarks_created_at_index"),
            IndexModel([("firebase_uid", ASCENDING), ("course_id", ASCENDING), ("lecture_id", ASCENDING), ("card_index", ASCENDING)], 
                      unique=True, name="user_bookmark_unique")
        ]
        
        try:
            await bookmarks_collection.create_indexes(bookmark_indexes)
            logger.info("✅ Created indexes for bookmarks collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("Bookmarks collection indexes already exist")
            else:
                logger.error(f"Error creating bookmark indexes: {e}")
        
        logger.info("🎉 Database indexing completed successfully!")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise
