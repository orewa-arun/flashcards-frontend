"""Health check endpoint."""

from fastapi import APIRouter
from app.database import get_database
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    try:
        # Test database connection
        db = get_database()
        if db is not None:
            # Ping the database to ensure it's accessible
            await db.command("ping")
            return {
                "status": "healthy",
                "database": "connected",
                "message": "Analytics API is running"
            }
        else:
            return {
                "status": "unhealthy", 
                "database": "disconnected",
                "message": "Database connection not available"
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error", 
            "message": f"Database connection failed: {str(e)}"
        }
