"""Health check endpoint using PostgreSQL."""

from fastapi import APIRouter
from app.db.postgres import get_postgres_pool
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    try:
        # Test PostgreSQL database connection
        pool = await get_postgres_pool()
        
        async with pool.acquire() as conn:
            # Simple query to verify connection
            result = await conn.fetchval("SELECT 1")
            
            if result == 1:
                return {
                    "status": "healthy",
                    "database": "connected",
                    "message": "Analytics API is running with PostgreSQL"
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
