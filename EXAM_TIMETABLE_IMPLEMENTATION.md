# Exam Timetable Implementation

## Overview

A timezone-aware exam timetable system that allows users to create and manage exam schedules for each course. All times are displayed and handled in **Indian Standard Time (IST)** while being stored in UTC in MongoDB.

## Key Features

✅ **Timezone-Aware**: All dates automatically converted between IST (user-facing) and UTC (database)  
✅ **User-Editable**: Any authenticated user can update the timetable  
✅ **Audit Trail**: Tracks who made the last update and when  
✅ **Clean UI**: Modern, intuitive interface for viewing and editing exam schedules  
✅ **Responsive**: Works seamlessly on desktop and mobile devices  

## Architecture

### Backend

#### Data Model (`backend/app/models/timetable.py`)

```python
{
  "course_id": "MS5031",
  "exams": [
    {
      "exam_id": "unique_id_1",
      "subject": "Midterm Exam",
      "date_utc": ISODate("2025-11-10T08:30:00Z"),  // 2 PM IST stored as UTC
      "notes": "Covers lectures 1-5"
    }
  ],
  "last_updated_by": {
    "user_id": "firebase_uid",
    "user_name": "Arun Kumar",
    "timestamp_utc": ISODate("2025-11-04T12:00:00Z")
  }
}
```

#### Service Layer (`backend/app/services/timetable_service.py`)

The `TimetableService` handles all timezone conversion logic:

- **`ist_to_utc(ist_datetime_str)`**: Converts IST datetime strings from frontend to UTC datetime objects for database storage
- **`utc_to_ist(utc_datetime)`**: Converts UTC datetime objects from database to IST datetime strings for frontend display
- **`get_timetable(course_id)`**: Fetches timetable and converts all dates to IST
- **`update_timetable(course_id, exams, user_id, user_name)`**: Saves timetable and converts all dates to UTC

**Timezone Handling:**
- Uses Python's `zoneinfo` module with `ZoneInfo("Asia/Kolkata")` for IST
- All conversions happen at the API boundaries (service layer)
- Database always stores UTC (industry best practice)
- Frontend always receives and sends IST

#### API Endpoints (`backend/app/routers/timetable.py`)

- **`GET /api/v1/timetables/{course_id}`**: Get timetable for a course (dates in IST)
- **`PUT /api/v1/timetables/{course_id}`**: Update timetable (accepts dates in IST)
- **`DELETE /api/v1/timetables/{course_id}/exams/{exam_id}`**: Delete a specific exam

### Frontend

#### API Service (`frontend/src/api/timetable.js`)

Simple API client that communicates with the backend:
- `getTimetable(courseId)`: Fetch timetable
- `updateTimetable(courseId, exams)`: Save timetable
- `deleteExam(courseId, examId)`: Remove an exam

#### View Component (`frontend/src/views/TimetableView.jsx`)

**Two Modes:**

1. **View Mode** (Default)
   - Displays all exams in a clean card layout
   - Shows last updated by information
   - Click "Edit Timetable" to switch to edit mode

2. **Edit Mode**
   - Add new exams with subject, date/time, and notes
   - Edit existing exams inline
   - Remove exams
   - Save or cancel changes

**Features:**
- Date/time picker for easy date selection
- Automatic IST formatting for display
- Real-time validation
- Responsive design

#### Styling (`frontend/src/views/TimetableView.css`)

Modern, clean design with:
- Card-based layout
- Smooth transitions and hover effects
- Color-coded buttons (blue for edit/save, green for add, red for delete)
- Responsive grid for edit fields
- Mobile-friendly breakpoints

## Usage

### Backend Setup

1. The timetable router is automatically registered in `app/main.py`
2. MongoDB collection `course_timetables` is automatically created on first use
3. No additional configuration needed

### Frontend Access

Navigate to a course timetable:
```
/courses/{courseId}/timetable
```

Example: `/courses/MS5031/timetable`

### Adding to Course Navigation

To add a "Exam Timetable" link to your course detail page:

```jsx
<Link to={`/courses/${courseId}/timetable`}>
  <FaCalendarAlt /> Exam Timetable
</Link>
```

## Timezone Strategy

### The Problem

- User in India: "My exam is on Nov 10 at 2:00 PM"
- Naive storage: `2025-11-10T14:00:00` (ambiguous - which timezone?)
- Wrong interpretation: Database assumes UTC → Displays as 7:30 PM IST (off by 5.5 hours!)

### The Solution

**Always Be Explicit:**

1. **Frontend → Backend**: User enters "Nov 10, 2:00 PM" → Frontend sends `"2025-11-10T14:00:00"` → Backend parses as IST → Converts to UTC → Stores `2025-11-10T08:30:00Z`

2. **Backend → Frontend**: Database has `2025-11-10T08:30:00Z` (UTC) → Backend converts to IST → Sends `"2025-11-10T14:00:00"` → Frontend displays "Nov 10, 2:00 PM"

**Result:** User always sees the correct time in IST, regardless of server location or database timezone.

## Testing

### Test Timezone Conversion

1. Add an exam with date "Nov 10, 2025 at 2:00 PM"
2. Check MongoDB directly:
   ```javascript
   db.course_timetables.findOne({course_id: "MS5031"})
   ```
3. Verify `date_utc` shows `2025-11-10T08:30:00Z` (8:30 AM UTC = 2:00 PM IST)

### Test Audit Trail

1. User A creates a timetable
2. Check "Last updated by" shows User A's name
3. User B edits the timetable
4. Check "Last updated by" now shows User B's name

## Future Enhancements

- [ ] Add notifications/reminders for upcoming exams
- [ ] Export timetable to calendar (iCal format)
- [ ] Add recurring exams (weekly quizzes, etc.)
- [ ] Filter exams by month/week
- [ ] Add exam duration and location fields
- [ ] Integrate with quiz history to show performance for each exam

