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
            IndexModel([("course_id", ASCENDING), ("deck_id", ASCENDING)], name="course_deck_bookmarks_index"),
            IndexModel([("created_at", ASCENDING)], name="bookmarks_created_at_index"),
            IndexModel([("firebase_uid", ASCENDING), ("course_id", ASCENDING), ("deck_id", ASCENDING), ("flashcard_index", ASCENDING)], 
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
        
        # User flashcard performance collection indexes (V2)
        flashcard_perf_collection = db.user_flashcard_performance
        flashcard_perf_indexes = [
            IndexModel([("user_id", ASCENDING), ("flashcard_id", ASCENDING)], 
                      unique=True, name="user_flashcard_unique"),
            IndexModel([("user_id", ASCENDING)], name="user_id_flashcard_perf_index"),
            IndexModel([("course_id", ASCENDING)], name="course_id_flashcard_perf_index"),
            IndexModel([("lecture_id", ASCENDING)], name="lecture_id_flashcard_perf_index"),
            IndexModel([("is_weak", ASCENDING)], name="is_weak_index"),
            IndexModel([("last_updated", ASCENDING)], name="flashcard_perf_updated_index")
        ]
        
        try:
            await flashcard_perf_collection.create_indexes(flashcard_perf_indexes)
            logger.info("✅ Created indexes for user_flashcard_performance collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("User flashcard performance collection indexes already exist")
            else:
                logger.error(f"Error creating flashcard performance indexes: {e}")
        
        # User exam readiness collection indexes (V2)
        exam_readiness_collection = db.user_exam_readiness
        exam_readiness_indexes = [
            IndexModel([("user_id", ASCENDING), ("exam_id", ASCENDING)], 
                      unique=True, name="user_exam_unique"),
            IndexModel([("user_id", ASCENDING)], name="user_id_exam_readiness_index"),
            IndexModel([("course_id", ASCENDING)], name="course_id_exam_readiness_index"),
            IndexModel([("last_calculated", ASCENDING)], name="last_calculated_index")
        ]
        
        try:
            await exam_readiness_collection.create_indexes(exam_readiness_indexes)
            logger.info("✅ Created indexes for user_exam_readiness collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("User exam readiness collection indexes already exist")
            else:
                logger.error(f"Error creating exam readiness indexes: {e}")
        
        # Mix sessions collection indexes
        mix_sessions_collection = db.mix_sessions
        mix_sessions_indexes = [
            IndexModel([("session_id", ASCENDING)], unique=True, name="session_id_unique"),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)], name="user_status_index"),
            IndexModel([("user_id", ASCENDING)], name="user_id_mix_sessions_index"),
            IndexModel([("created_at", ASCENDING)], name="mix_sessions_created_at_index"),
            IndexModel([("last_updated", ASCENDING)], name="mix_sessions_updated_index")
        ]
        
        try:
            await mix_sessions_collection.create_indexes(mix_sessions_indexes)
            logger.info("✅ Created indexes for mix_sessions collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("Mix sessions collection indexes already exist")
            else:
                logger.error(f"Error creating mix sessions indexes: {e}")
        
        # User question performance collection indexes
        question_perf_collection = db.user_question_performance
        question_perf_indexes = [
            IndexModel([("user_id", ASCENDING), ("question_content_hash", ASCENDING)], 
                      unique=True, name="user_question_unique"),
            IndexModel([("user_id", ASCENDING)], name="user_id_question_perf_index"),
            IndexModel([("flashcard_id", ASCENDING)], name="flashcard_id_question_perf_index"),
            IndexModel([("last_attempted", ASCENDING)], name="question_perf_last_attempted_index")
        ]
        
        try:
            await question_perf_collection.create_indexes(question_perf_indexes)
            logger.info("✅ Created indexes for user_question_performance collection")
        except OperationFailure as e:
            if "already exists" in str(e):
                logger.info("User question performance collection indexes already exist")
            else:
                logger.error(f"Error creating question performance indexes: {e}")
        
        logger.info("🎉 Database indexing completed successfully!")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise
