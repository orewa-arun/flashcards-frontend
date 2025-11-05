"""Service layer for course exam timetables with timezone-aware operations."""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# IST timezone (India Standard Time)
IST = ZoneInfo("Asia/Kolkata")


class TimetableService:
    """Service for managing course exam timetables with IST timezone support."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.course_timetables
    
    async def initialize_indexes(self):
        """Create indexes for efficient querying."""
        await self.collection.create_index("course_id", unique=True)
        logger.info("Course timetable indexes created")
    
    @staticmethod
    def ist_to_utc(ist_datetime_str: str) -> datetime:
        """
        Convert IST datetime string to UTC datetime object.
        
        Args:
            ist_datetime_str: DateTime string in IST (e.g., "2025-11-10T14:00:00")
            
        Returns:
            datetime object in UTC
        """
        try:
            # Parse the datetime string (assumes no timezone info in string)
            dt_naive = datetime.fromisoformat(ist_datetime_str)
            
            # Localize to IST
            dt_ist = dt_naive.replace(tzinfo=IST)
            
            # Convert to UTC
            dt_utc = dt_ist.astimezone(timezone.utc)
            
            return dt_utc
        
        except Exception as e:
            logger.error(f"Error converting IST to UTC: {e}")
            raise ValueError(f"Invalid datetime format: {ist_datetime_str}")
    
    @staticmethod
    def utc_to_ist(utc_datetime: datetime) -> str:
        """
        Convert UTC datetime object to IST datetime string.
        
        Args:
            utc_datetime: datetime object in UTC
            
        Returns:
            DateTime string in IST format
        """
        try:
            # Ensure the datetime is timezone-aware (UTC)
            if utc_datetime.tzinfo is None:
                utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
            
            # Convert to IST
            dt_ist = utc_datetime.astimezone(IST)
            
            # Return as ISO format string without timezone suffix
            return dt_ist.strftime("%Y-%m-%dT%H:%M:%S")
        
        except Exception as e:
            logger.error(f"Error converting UTC to IST: {e}")
            return utc_datetime.isoformat()
    
    async def get_timetable(self, course_id: str) -> Optional[Dict[str, Any]]:
        """
        Get exam timetable for a course, converting all UTC times to IST.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Timetable document with dates converted to IST, or None if not found
        """
        timetable = await self.collection.find_one({"course_id": course_id})
        
        if not timetable:
            logger.info(f"No timetable found for course {course_id}")
            return None
        
        # Convert UTC dates to IST for all exams
        if timetable.get('exams'):
            for exam in timetable['exams']:
                if 'date_utc' in exam:
                    exam['date_ist'] = self.utc_to_ist(exam['date_utc'])
                    # Remove the UTC field for frontend
                    del exam['date_utc']
        
        # Convert last_updated_by timestamp to IST
        if timetable.get('last_updated_by') and 'timestamp_utc' in timetable['last_updated_by']:
            timetable['last_updated_by']['timestamp_ist'] = self.utc_to_ist(
                timetable['last_updated_by']['timestamp_utc']
            )
            del timetable['last_updated_by']['timestamp_utc']
        
        # Remove MongoDB _id field
        if '_id' in timetable:
            del timetable['_id']
        
        logger.info(f"Retrieved timetable for course {course_id} with {len(timetable.get('exams', []))} exams")
        return timetable
    
    async def update_timetable(
        self,
        course_id: str,
        exams: List[Dict[str, Any]],
        user_id: str,
        user_name: str
    ) -> bool:
        """
        Update exam timetable for a course, converting IST times to UTC.
        
        Args:
            course_id: Course identifier
            exams: List of exam dictionaries with IST datetime strings
            user_id: ID of user making the update
            user_name: Display name of user making the update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert all IST dates to UTC
            processed_exams = []
            for exam in exams:
                processed_exam = exam.copy()
                
                # Convert date from IST to UTC
                if 'date_ist' in processed_exam:
                    processed_exam['date_utc'] = self.ist_to_utc(processed_exam['date_ist'])
                    del processed_exam['date_ist']
                
                # Ensure exam_id exists
                if 'exam_id' not in processed_exam:
                    processed_exam['exam_id'] = str(datetime.utcnow().timestamp())
                
                processed_exams.append(processed_exam)
            
            # Prepare the update document
            update_doc = {
                "course_id": course_id,
                "exams": processed_exams,
                "last_updated_by": {
                    "user_id": user_id,
                    "user_name": user_name,
                    "timestamp_utc": datetime.utcnow()
                }
            }
            
            # Upsert the timetable (create if doesn't exist, update if it does)
            result = await self.collection.replace_one(
                {"course_id": course_id},
                update_doc,
                upsert=True
            )
            
            logger.info(f"✅ Updated timetable for course {course_id} by {user_name} ({user_id})")
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
            result = await self.collection.update_one(
                {"course_id": course_id},
                {"$pull": {"exams": {"exam_id": exam_id}}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Deleted exam {exam_id} from course {course_id}")
                return True
            else:
                logger.warning(f"No exam found with id {exam_id} in course {course_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting exam {exam_id} from course {course_id}: {e}")
            return False

