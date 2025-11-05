# The Trinity Engine - Quick Start Guide

## What is The Trinity Engine?

The Trinity Engine is the **Exam Readiness Score** system - a sophisticated, multi-dimensional intelligence layer that transforms raw quiz data into actionable exam preparation insights.

### The Three Pillars (The Trinity)

```
📚 COVERAGE (50%)     🎯 MASTERY (30%)      ⚡ MOMENTUM (20%)
Have you seen         How well do you        Are you peaking
all the material?     know it?               at the right time?
```

---

## For Users: How It Works

### Step 1: Take Quizzes
- Practice with flashcards and quizzes for your enrolled courses
- All difficulty levels contribute to your readiness score

### Step 2: View Your Readiness
- Navigate to **"My Schedule"** or **Course Timetable**
- Each exam displays a colored ring:
  - 🟢 **Green (≥75%)**: You're ready!
  - 🟠 **Orange (50-74%)**: Keep practicing
  - 🔴 **Red (<50%)**: Critical - focus here!

### Step 3: Click for Details
- Click the ring to see your Trinity breakdown
- Get personalized recommendations
- One-click action buttons to practice weak areas

### Step 4: Improve & Repeat
- Follow the recommendations
- Take targeted quizzes
- Watch your readiness score improve in real-time

---

## For Developers: Quick Integration

### Backend: Calculate Readiness

```python
from app.services.exam_readiness_service import ExamReadinessService

readiness_service = ExamReadinessService(mongodb)
readiness = await readiness_service.calculate_exam_readiness(
    user_id="firebase_uid",
    course_id="MS5031",
    exam_id="midterm_exam_1",
    exam_lectures=["DAA_lec_1", "DAA_lec_4", "DAA_lec_7"]
)

print(f"Overall: {readiness.overall_score}%")
print(f"Recommendation: {readiness.recommendation}")
```

### Frontend: Display Readiness

```jsx
import ReadinessRing from '../components/ReadinessRing';

// In your component
<ReadinessRing 
  courseId="MS5031"
  examId="midterm_exam_1"
  examName="Midterm Exam"
/>
```

---

## API Endpoint

### GET Exam Readiness

```
GET /api/v1/timetables/{course_id}/exams/{exam_id}/readiness
```

**Example Request:**
```bash
curl -X GET \
  'http://localhost:8000/api/v1/timetables/MS5031/exams/midterm_exam_1/readiness' \
  -H 'Authorization: Bearer YOUR_FIREBASE_TOKEN'
```

**Example Response:**
```json
{
  "overall_score": 67.5,
  "breakdown": {
    "coverage": {
      "score": 85.0,
      "details": "You've been quizzed on 17 out of 20 concepts for this exam."
    },
    "mastery": {
      "score": 72.5,
      "details": "You've earned 145 out of 200 weighted points across all difficulty levels."
    },
    "momentum": {
      "score": 55.0,
      "details": "Your recent performance shows 55% accuracy, with recent attempts weighted more heavily."
    }
  },
  "recommendation": "Your accuracy needs improvement. Let's reinforce the concepts you're struggling with.",
  "action_type": "mastery",
  "urgency_level": "medium",
  "covered_lectures": ["DAA_lec_1", "DAA_lec_4"],
  "uncovered_lectures": ["DAA_lec_7"],
  "weak_lectures": ["DAA_lec_4"]
}
```

---

## The Math Behind The Magic

### Coverage Score
```
covered_flashcards = flashcards user has been quizzed on
total_flashcards = all flashcards in exam lectures

Coverage = (covered / total) × 100
```

### Mastery Score (Weighted)
```
Level Weights:
- Easy: 1 point
- Medium: 2 points
- Hard: 3 points
- Boss: 4 points

Mastery = (earned_weighted_points / max_weighted_points) × 100
```

### Momentum Score (Time-Decayed)
```
Decay Factor = e^(-ln(2) × days_since_attempt / 7)

Recent attempts count more than old attempts
Half-life: 7 days

Momentum = (weighted_correct / weighted_total) × 100
```

### Overall Score
```
Overall = (Coverage × 0.5) + (Mastery × 0.3) + (Momentum × 0.2)
```

---

## File Structure

```
backend/
├── app/
│   ├── models/
│   │   └── exam_readiness.py         # Pydantic models
│   ├── services/
│   │   └── exam_readiness_service.py # Trinity Engine logic
│   └── routers/
│       └── timetable.py               # API endpoint

frontend/
├── src/
│   ├── api/
│   │   └── examReadiness.js          # API service
│   ├── components/
│   │   ├── ReadinessRing.jsx         # Circular progress UI
│   │   ├── ReadinessRing.css
│   │   ├── ReadinessBreakdownModal.jsx  # Detailed view
│   │   └── ReadinessBreakdownModal.css
│   └── views/
│       ├── TimetableView.jsx         # Course timetable (integrated)
│       └── MyScheduleView.jsx        # Aggregated schedule (integrated)
```

---

## Key Dependencies

### Backend
- `motor` (MongoDB async driver)
- `pydantic` (Data validation)
- `fastapi` (API framework)

### Frontend
- `react` & `react-router-dom`
- `axios` (API calls)
- `react-icons` (UI icons)

---

## Testing Your Implementation

### 1. Backend Test
```bash
# Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# Test endpoint
curl -X GET 'http://localhost:8000/api/v1/timetables/MS5031/exams/test_exam/readiness' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### 2. Frontend Test
```bash
# Start frontend
cd frontend
npm run dev

# Navigate to:
# http://localhost:5173/courses/MS5031/timetable
# or
# http://localhost:5173/my-schedule

# Look for the colored readiness rings next to each exam
# Click them to see the breakdown modal
```

### 3. Verify Data Flow
1. Take a quiz in any level (easy/medium/hard/boss)
2. Go to timetable page
3. Click readiness ring
4. Verify:
   - Coverage shows quizzed flashcards
   - Mastery reflects your accuracy
   - Momentum shows recent performance
   - Recommendation is actionable

---

## Troubleshooting

### "Readiness Ring shows error (!)"
- Check that the exam has `lectures` field populated in timetable
- Verify flashcards exist for those lectures (`*_cognitive_flashcards_only.json`)
- Check backend logs for detailed error

### "Score is always 0%"
- Ensure you've taken at least one quiz for the course
- Verify quiz attempts are saving to MongoDB (`quiz_attempts` collection)
- Check that `source_flashcard_id` is present in quiz attempts

### "Modal action button does nothing"
- Verify the lecture route exists: `/courses/{courseId}/lectures/{lectureId}/quiz`
- Check browser console for navigation errors

---

## Next Steps

1. **Deploy to Production**
   - Set up MongoDB indexes on `quiz_attempts` collection
   - Configure environment variables for production API URL
   - Test with real user data

2. **Monitor Key Metrics**
   - Engagement rate (% who click rings)
   - Action conversion (% who click modal buttons)
   - Score improvement over time

3. **Iterate Based on Data**
   - Adjust Trinity weights if needed
   - Refine recommendation logic
   - Add historical tracking (score over time)

---

## The Vision

The Trinity Engine is not just a score. It's a **flywheel**:

```
Low Score → Recommendation → Targeted Practice → Score Improves → User Returns
                                    ↑___________________________↓
```

This drives engagement, retention, and ultimately, **student success**.

---

**Built with conviction.**  
**Shipped with urgency.**  
**Optimized for impact.**

