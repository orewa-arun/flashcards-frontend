"""Data models for course exam timetables."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ExamEntry(BaseModel):
    """Individual exam entry in the timetable."""
    exam_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    subject: str
    date_utc: datetime  # Stored in UTC, converted to/from IST at API boundaries
    lectures: Optional[List[str]] = None  # Optional list of lecture IDs covered in this exam
    notes: Optional[str] = None


class LastUpdatedBy(BaseModel):
    """Audit trail for who last modified the timetable."""
    user_id: str
    user_name: str
    timestamp_utc: datetime


class CourseTimetable(BaseModel):
    """Complete timetable for a course."""
    course_id: str
    exams: List[ExamEntry] = Field(default_factory=list)
    last_updated_by: Optional[LastUpdatedBy] = None


class TimetableUpdateRequest(BaseModel):
    """Request model for updating a course timetable."""
    exams: List[dict]  # Frontend sends IST date strings, backend converts to UTC


class TimetableResponse(BaseModel):
    """Response model for timetable API."""
    course_id: str
    exams: List[dict]  # Backend sends IST date strings
    last_updated_by: Optional[dict] = None

