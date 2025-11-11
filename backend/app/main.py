"""FastAPI application for analytics backend."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import (
    health,
    auth,
    bookmarks,
    feedback,
    quiz_history,
    admin_analytics,
    quiz,
    adaptive_quiz,
    timetable,
    profile,
    performance,
    mix_mode
)
from app.firebase_auth import initialize_firebase
from app.database_indexes import create_indexes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up Analytics API...")
    await connect_to_mongo()
    initialize_firebase()
    
    # Create database indexes
    from app.database import get_database
    db = get_database()
    await create_indexes(db)
    yield
    # Shutdown
    logger.info("Shutting down Analytics API...")
    await close_mongo_connection()

# Create FastAPI application
app = FastAPI(
    title="Study Analytics API",
    description="Analytics backend for tracking study progress and quiz results",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(bookmarks.router)
app.include_router(feedback.router)
app.include_router(quiz_history.router)
app.include_router(admin_analytics.router)
app.include_router(quiz.router)
app.include_router(adaptive_quiz.router)
app.include_router(timetable.router)
app.include_router(profile.router)
app.include_router(performance.router, prefix="/api/v1/performance", tags=["performance"])
app.include_router(mix_mode.router)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Study Analytics API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
