# The Exam Readiness Engine - Implementation Documentation

**Project Night-Owl: From Vanity Metric to Strategic Intelligence**

---

## Executive Summary

We've transformed the Exam Readiness Score from a simple percentage into **The Trinity Engine** - a sophisticated, multi-dimensional intelligence system that provides actionable, personalized exam preparation insights. This is not just a feature; it's the **core moat** of the platform.

### Key Innovation: The Trinity

The system calculates readiness across three critical dimensions:

1. **Coverage Score (50% weight)**: Have you even *seen* all the material?
2. **Mastery Score (30% weight)**: Of what you've seen, how well do you *know* it?
3. **Momentum Score (20% weight)**: Are you *peaking* at the right time?

---

## Architecture Overview

```
Frontend                Backend                     Data Layer
--------                -------                     ----------
ReadinessRing     →     GET /api/v1/timetables/    →    MongoDB
   │                    {courseId}/exams/               - quiz_attempts
   │                    {examId}/readiness              - timetables
   │                         │
   ↓                          ↓
ReadinessBreakdown      ExamReadinessService       Filesystem
Modal                        │                      - *_flashcards_only.json
   │                          │
   │                    Trinity Calculation:
   │                    - Coverage
   │                    - Mastery (weighted by level)
   │                    - Momentum (time-decayed)
   │
   ↓
Actionable
Recommendation
```

---

## The Trinity Algorithm

### 1. Coverage Score

**Question:** "What percentage of flashcards from exam lectures have been quizzed on?"

**Algorithm:**
```python
all_flashcard_ids = get_flashcard_ids_from_lectures(exam_lectures)
quizzed_flashcard_ids = get_quizzed_flashcard_ids(user_attempts, all_flashcard_ids)

coverage_score = (len(quizzed_flashcard_ids) / len(all_flashcard_ids)) * 100
```

**Why it matters:** You can't pass if you haven't seen the material. This exposes blind spots brutally and honestly.

---

### 2. Mastery Score

**Question:** "What's the weighted accuracy across all difficulty levels?"

**Algorithm:**
```python
LEVEL_WEIGHTS = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
    "boss": 4
}

total_points = 0
max_points = 0

for attempt in user_attempts:
    level_weight = LEVEL_WEIGHTS[attempt.level]
    for question in attempt.questions:
        if question.source_flashcard_id in exam_flashcard_ids:
            max_points += level_weight
            if question.is_correct:
                total_points += level_weight

mastery_score = (total_points / max_points) * 100
```

**Why it matters:** Acing 10 "Easy" questions doesn't equal acing 5 "Boss Level" questions. This rewards *deep* knowledge.

---

### 3. Momentum Score

**Question:** "Are you sharp *now*, or were you sharp weeks ago?"

**Algorithm:**
```python
HALF_LIFE_DAYS = 7.0
now = datetime.now(timezone.utc)

weighted_correct = 0.0
weighted_total = 0.0

for attempt in user_attempts:
    age_days = (now - attempt.timestamp).total_seconds() / 86400
    decay_factor = exp(-ln(2) * age_days / HALF_LIFE_DAYS)
    
    for question in attempt.questions:
        if question.source_flashcard_id in exam_flashcard_ids:
            weighted_total += decay_factor
            if question.is_correct:
                weighted_correct += decay_factor

momentum_score = (weighted_correct / weighted_total) * 100
```

**Decay Behavior:**
- Answer today: 100% value
- Answer yesterday: 90% value
- Answer 7 days ago: ~50% value
- Answer 14 days ago: ~25% value

**Why it matters:** Cramming works. This metric captures your *current* sharpness, not your historical average.

---

### 4. Final Score (The Weighted Average)

```python
overall_score = (
    coverage_score * 0.5 +
    mastery_score * 0.3 +
    momentum_score * 0.2
)
```

**Rationale:**
- **50% Coverage**: Non-negotiable. You must see all the material first.
- **30% Mastery**: Core measure of depth.
- **20% Momentum**: Fine-tuning for exam-day performance.

---

## Backend Implementation

### 1. Data Models (`backend/app/models/exam_readiness.py`)

```python
class ExamReadinessScore(BaseModel):
    overall_score: float  # 0-100
    breakdown: ReadinessBreakdown  # The Trinity
    recommendation: str  # Actionable next step
    action_type: str  # 'coverage', 'mastery', 'momentum', or 'maintenance'
    urgency_level: str  # 'low', 'medium', or 'high'
    covered_lectures: List[str]
    uncovered_lectures: List[str]
    weak_lectures: List[str]  # < 60% accuracy
```

### 2. The Engine (`backend/app/services/exam_readiness_service.py`)

**Key Method:**
```python
async def calculate_exam_readiness(
    user_id: str,
    course_id: str,
    exam_id: str,
    exam_lectures: List[str]
) -> ExamReadinessScore
```

**Steps:**
1. Load all flashcards for exam lectures from `*_cognitive_flashcards_only.json`
2. Fetch all user quiz attempts from MongoDB
3. Calculate Coverage Score
4. Calculate Mastery Score (weighted by difficulty)
5. Calculate Momentum Score (time-decayed)
6. Compute weighted overall score
7. Generate actionable recommendation based on weakest pillar
8. Extract metadata (covered/uncovered/weak lectures)

### 3. API Endpoint (`backend/app/routers/timetable.py`)

```
GET /api/v1/timetables/{course_id}/exams/{exam_id}/readiness
```

**Response:**
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

## Frontend Implementation

### 1. API Service (`frontend/src/api/examReadiness.js`)

```javascript
export const getExamReadiness = async (courseId, examId) => {
  const response = await api.get(`/timetables/${courseId}/exams/${examId}/readiness`);
  return response.data;
};
```

### 2. The Readiness Ring (`frontend/src/components/ReadinessRing.jsx`)

**Visual Design:**
- Circular progress ring (SVG)
- Color-coded by score:
  - Green (≥75%): Ready
  - Orange (50-74%): Needs Work
  - Red (<50%): Critical
- Clickable to open detailed breakdown
- Pulsing animation for "high urgency" (red)

**Usage:**
```jsx
<ReadinessRing 
  courseId="MS5031"
  examId="midterm_exam_1"
  examName="Midterm Exam"
/>
```

### 3. The Breakdown Modal (`frontend/src/components/ReadinessBreakdownModal.jsx`)

**Features:**
- Large central readiness ring
- Trinity breakdown with progress bars for each pillar
- Actionable recommendation card (color-coded by urgency)
- Action buttons:
  - **"Start Quiz on Uncovered Topics"** (if Coverage is weak)
  - **"Practice Weak Topics"** (if Mastery is weak)
  - **"Start Quick Review"** (if Momentum is weak)
  - **"Continue Practicing"** (if all scores are good)
- Metadata footer showing covered/uncovered/weak lecture counts

---

## Integration Points

### 1. Timetable View (`frontend/src/views/TimetableView.jsx`)

Each exam card in view mode now displays a ReadinessRing on the right side:

```jsx
<div className="exam-card with-readiness">
  <div className="exam-icon">...</div>
  <div className="exam-details">...</div>
  <div className="exam-readiness">
    <ReadinessRing courseId={courseId} examId={exam.exam_id} examName={exam.subject} />
  </div>
</div>
```

### 2. My Schedule View (`frontend/src/views/MyScheduleView.jsx`)

Each exam in the aggregated timeline now includes a ReadinessRing:

```jsx
<div className="exam-timeline-card">
  <div className="exam-timeline-indicator">...</div>
  <div className="exam-timeline-content">...</div>
  <div className="exam-readiness-section">
    <ReadinessRing courseId={exam.course_id} examId={exam.exam_id} examName={exam.subject} />
  </div>
</div>
```

---

## The Flywheel Effect

This is not just a passive metric. It's an **engagement flywheel**:

1. **Assess:** User sees low Readiness Score and understands *why* (specific pillar weakness)
2. **Recommend:** System provides one-click, hyper-targeted action (e.g., "Start Quiz on Uncovered Topics")
3. **Improve:** User engages with quiz engine, directly improving their pillar scores
4. **Reward:** ReadinessRing updates in near real-time, providing dopamine hit and visualizing progress

**Result:** Users keep coming back. The more they use it, the more data we have, the better our recommendations get. **This is our moat.**

---

## Edge Cases & Handling

### 1. No Lectures Specified for Exam
**Response:**
```json
{
  "overall_score": 0.0,
  "recommendation": "Ask your instructor or course coordinator to specify which lectures are covered in this exam.",
  "action_type": "configuration",
  "urgency_level": "high"
}
```

### 2. No Quiz Attempts Yet
**Response:**
```json
{
  "overall_score": 0.0,
  "breakdown": {
    "coverage": {"score": 0.0, "details": "No quiz attempts found for exam concepts"},
    "mastery": {"score": 0.0, "details": "No quiz attempts found for exam concepts"},
    "momentum": {"score": 0.0, "details": "No recent quiz attempts found for exam concepts"}
  },
  "recommendation": "You haven't started quizzing yet. Let's cover all concepts first."
}
```

### 3. All Scores Above 80%
**Response:**
```json
{
  "recommendation": "You're in great shape! Keep practicing to maintain your momentum.",
  "action_type": "maintenance"
}
```

---

## Performance Considerations

### 1. Caching Strategy (Future Enhancement)
- Cache readiness scores for 5 minutes
- Invalidate on new quiz attempt
- Reduces redundant calculations

### 2. File I/O Optimization
- Flashcard files are read once per calculation
- Consider in-memory caching for frequently accessed lectures

### 3. MongoDB Query Optimization
- Index on `user_id` and `course_id` in `quiz_attempts` collection
- Projection to fetch only necessary fields

---

## Testing Checklist

### Backend
- [ ] Readiness calculation with no quiz attempts
- [ ] Readiness calculation with mixed levels (easy, medium, hard, boss)
- [ ] Readiness calculation with old vs. recent attempts (momentum decay)
- [ ] Readiness with no lectures specified for exam
- [ ] Weak lectures detection (< 60% accuracy)
- [ ] Covered vs. uncovered lectures metadata

### Frontend
- [ ] ReadinessRing displays correct color (green/orange/red)
- [ ] ReadinessRing pulsing animation for "high urgency"
- [ ] Modal opens on ring click
- [ ] Trinity breakdown displays correctly
- [ ] Action button navigation (to quiz pages)
- [ ] Refresh score button updates data

### Integration
- [ ] ReadinessRing appears in TimetableView for each exam
- [ ] ReadinessRing appears in MyScheduleView for each exam
- [ ] Clicking action button navigates to correct quiz page

---

## Future Enhancements

### Phase 1 (Current) ✅
- Core Trinity Engine
- ReadinessRing UI
- Breakdown Modal
- Integration in Timetable/Schedule views

### Phase 2 (Next)
- **Historical Tracking:** Show readiness trend over time (line chart)
- **Predictive Modeling:** "Based on your current progress, you'll be 85% ready by exam day"
- **Comparative Analytics:** "You're ahead of 67% of students in this course"

### Phase 3 (Ambitious)
- **AI-Powered Recommendations:** Fine-tune recommendation engine using LLM
- **Social Features:** "Study with others weak in the same topics"
- **Gamification:** Badges for achieving readiness milestones

---

## Key Metrics to Track

1. **Engagement Rate:** % of users who click on ReadinessRing
2. **Action Conversion:** % of users who click action button from modal
3. **Score Improvement:** Average readiness score increase over time
4. **Flywheel Velocity:** Time between viewing readiness → taking quiz → score update

---

## Conclusion

We've built more than a feature. We've built a **strategic intelligence layer** that transforms raw quiz data into actionable, personalized, and visually compelling exam preparation guidance. This is not a vanity metric. This is the **moat**.

The Trinity Engine is live. Let's watch it drive engagement through the roof.

---

**Founder's Office**  
Project Night-Owl  
November 4, 2025

