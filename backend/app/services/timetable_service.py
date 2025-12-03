"""Service layer for course exam timetables with timezone-aware operations using PostgreSQL."""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
import asyncpg
from zoneinfo import ZoneInfo
from dateutil import parser as date_parser

from app.repositories.quiz_repository import QuizRepository

logger = logging.getLogger(__name__)

# Supported timezones
TIMEZONES = {
    "Asia/Kolkata": ZoneInfo("Asia/Kolkata"),  # IST - India
    "Europe/Paris": ZoneInfo("Europe/Paris"),   # CET/CEST - France
    "UTC": ZoneInfo("UTC"),
}

# Default timezone (IST for backwards compatibility)
DEFAULT_TIMEZONE = "Asia/Kolkata"


def get_timezone(tz_name: str) -> ZoneInfo:
    """Get ZoneInfo object for timezone name, with fallback to default."""
    if tz_name in TIMEZONES:
        return TIMEZONES[tz_name]
    
    try:
        return ZoneInfo(tz_name)
    except Exception:
        logger.warning(f"Unknown timezone {tz_name}, using default {DEFAULT_TIMEZONE}")
        return TIMEZONES[DEFAULT_TIMEZONE]


class TimetableService:
    """Service for managing course exam timetables with dynamic timezone support using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool, user_timezone: str = DEFAULT_TIMEZONE):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
            user_timezone: User's timezone (e.g., 'Asia/Kolkata', 'Europe/Paris')
        """
        self.pool = pool
        self.repository = QuizRepository(pool)
        self.user_timezone = user_timezone
        self.user_tz = get_timezone(user_timezone)
    
    @staticmethod
    def local_to_utc(local_datetime_str: str, tz_name: str = DEFAULT_TIMEZONE) -> datetime:
        """
        Convert local datetime string to UTC datetime object.
        
        Args:
            local_datetime_str: DateTime string in local time (e.g., "2025-11-10T14:00:00")
            tz_name: Source timezone name
            
        Returns:
            datetime object in UTC
        """
        try:
            # Parse the datetime string (assumes no timezone info in string)
            dt_naive = datetime.fromisoformat(local_datetime_str)
            
            # Localize to the source timezone
            source_tz = get_timezone(tz_name)
            dt_local = dt_naive.replace(tzinfo=source_tz)
            
            # Convert to UTC
            dt_utc = dt_local.astimezone(timezone.utc)
            
            return dt_utc
        
        except Exception as e:
            logger.error(f"Error converting local to UTC: {e}")
            raise ValueError(f"Invalid datetime format: {local_datetime_str}")
    
    @staticmethod
    def utc_to_local(utc_datetime: Union[datetime, str], tz_name: str = DEFAULT_TIMEZONE) -> str:
        """
        Convert UTC datetime to local datetime string.
        
        Args:
            utc_datetime: datetime object or ISO string in UTC
            tz_name: Target timezone name
            
        Returns:
            DateTime string in local format
        """
        try:
            # Handle string input (from JSON/DB)
            if isinstance(utc_datetime, str):
                try:
                    utc_datetime = date_parser.parse(utc_datetime)
                except Exception:
                    logger.warning(f"Could not parse datetime string: {utc_datetime}")
                    return utc_datetime  # Return as-is if unparseable
            
            # Ensure the datetime is timezone-aware (UTC)
            if utc_datetime.tzinfo is None:
                utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
            
            # Convert to target timezone
            target_tz = get_timezone(tz_name)
            dt_local = utc_datetime.astimezone(target_tz)
            
            # Return as ISO format string without timezone suffix
            return dt_local.strftime("%Y-%m-%dT%H:%M:%S")
        
        except Exception as e:
            logger.error(f"Error converting UTC to local: {e}")
            # Return as-is if conversion fails
            if isinstance(utc_datetime, datetime):
                return utc_datetime.isoformat()
            return str(utc_datetime)
    
    # Legacy methods for backwards compatibility
    def ist_to_utc(self, ist_datetime_str: str) -> datetime:
        """Convert IST datetime string to UTC. (Legacy - use local_to_utc)"""
        return self.local_to_utc(ist_datetime_str, "Asia/Kolkata")
    
    def utc_to_ist(self, utc_datetime: Union[datetime, str]) -> str:
        """Convert UTC to IST string. (Legacy - use utc_to_local)"""
        return self.utc_to_local(utc_datetime, "Asia/Kolkata")
    
    async def get_timetable(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exam timetable for a course, converting all UTC times to user's timezone.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Timetable document with dates converted to user's timezone, or None if not found
        """
        timetable = await self.repository.get_timetable(course_id)
        
        if not timetable:
            logger.info(f"No timetable found for course {course_id}")
            return None
        
        # Convert UTC dates to user's local timezone for all exams
        if timetable.get('exams'):
            for exam in timetable['exams']:
                if 'date_utc' in exam and exam['date_utc']:
                    # Use the user's timezone for conversion
                    exam['date_ist'] = self.utc_to_local(exam['date_utc'], self.user_timezone)
                    # Remove the UTC field for frontend
                    del exam['date_utc']
        
        # Remove internal fields
        if 'id' in timetable:
            del timetable['id']
        
        logger.info(f"Retrieved timetable for course {course_id} with {len(timetable.get('exams', []))} exams (tz={self.user_timezone})")
        return timetable
    
    async def update_timetable(
        self,
        course_id: str,
        exams: List[Dict[str, Any]],
        user_id: str,
        user_name: str
    ) -> bool:
        """
        Update exam timetable for a course, converting local times to UTC.
        
        Args:
            course_id: Course identifier
            exams: List of exam dictionaries with local datetime strings (date_ist field)
            user_id: ID of user making the update
            user_name: Display name of user making the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert all local dates to UTC
            processed_exams = []
            for exam in exams:
                processed_exam = exam.copy()
                
                # Convert date from user's timezone to UTC
                if 'date_ist' in processed_exam:
                    # Use user's timezone for conversion (date_ist is actually user's local time)
                    utc_dt = self.local_to_utc(processed_exam['date_ist'], self.user_timezone)
                    processed_exam['date_utc'] = utc_dt.isoformat()
                    del processed_exam['date_ist']
                
                # Ensure exam_id exists
                if 'exam_id' not in processed_exam:
                    processed_exam['exam_id'] = str(datetime.utcnow().timestamp())
                
                processed_exams.append(processed_exam)
            
            # Save to PostgreSQL
            await self.repository.save_timetable(course_id, processed_exams)
            
            logger.info(f"Updated timetable for course {course_id} by {user_name} ({user_id}) (tz={self.user_timezone})")
            return True
        
        except Exception as e:
            logger.error(f"Error updating timetable for course {course_id}: {e}")
            return False
    
    async def delete_exam(self, course_id: str, exam_id: str) -> bool:
        """
        Delete a specific exam from a course timetable.
        
        Args:
            course_id: Course identifier
            exam_id: Exam identifier to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current timetable
            timetable = await self.repository.get_timetable(course_id)
            
            if not timetable:
                logger.warning(f"No timetable found for course {course_id}")
                return False
            
            # Filter out the exam to delete
            current_exams = timetable.get('exams', [])
            new_exams = [e for e in current_exams if e.get('exam_id') != exam_id]
            
            if len(new_exams) == len(current_exams):
                logger.warning(f"No exam found with id {exam_id} in course {course_id}")
                return False
            
            # Save updated exams
            await self.repository.save_timetable(course_id, new_exams)
            
            logger.info(f"Deleted exam {exam_id} from course {course_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting exam {exam_id} from course {course_id}: {e}")
            return False


async def get_timetable_service(user_timezone: str = DEFAULT_TIMEZONE) -> TimetableService:
    """
    Get timetable service instance with PostgreSQL pool.
    
    Args:
        user_timezone: User's timezone (e.g., 'Asia/Kolkata', 'Europe/Paris')
        
    Returns:
        TimetableService instance configured for the user's timezone
    """
    from app.db.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    return TimetableService(pool, user_timezone)
