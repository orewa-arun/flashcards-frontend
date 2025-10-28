# Adaptive Quiz Engine - Quick Start Guide

## 🚀 Getting Started

This guide will help you get the adaptive quiz engine up and running in minutes.

## Prerequisites

- Python 3.8+ (for backend)
- Node.js 16+ (for frontend)
- MongoDB instance (local or cloud)
- Backend and frontend dependencies installed

## Step 1: Environment Setup

### Backend Configuration

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Ensure your `.env` file has MongoDB configured:
   ```env
   MONGODB_URL=mongodb://localhost:27017
   # or for cloud MongoDB:
   # MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
   
   DATABASE_NAME=study_analytics
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=True
   ```

3. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Configuration

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Create `.env` file if it doesn't exist:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

3. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

## Step 2: Start the Servers

### Terminal 1 - Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Connected to MongoDB database: study_analytics
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

## Step 3: Test the Quiz Engine

### Option A: Manual Testing (Recommended for First Time)

1. Open your browser to http://localhost:5173
2. Navigate to a course (e.g., "Management Information Systems")
3. Click on a lecture (e.g., "MIS Lecture 4")
4. Study the flashcards (or skip to the last one using arrow keys)
5. Click "Start Quiz" button
6. Answer the 20 questions
7. Observe the checkpoint at question 15
8. View your results and weak concepts
9. Take the quiz again to see adaptive behavior

### Option B: Automated API Testing

Run the test script:
```bash
cd /Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai
python test_quiz_api.py
```

This will:
- Generate a first quiz
- Submit answers (50% correct)
- Generate a second quiz (adaptive)
- Display results for each step

## Step 4: Verify Features

### ✅ Checklist

After completing a quiz, verify:

1. **Quiz Generation**
   - [ ] Quiz loads with 20 questions (or 10 for small decks)
   - [ ] Questions are from different concepts
   - [ ] Progress bar updates correctly

2. **Question Types**
   - [ ] Multiple Choice questions work
   - [ ] Scenario-based MCQ displays scenario
   - [ ] Sequencing allows reordering
   - [ ] Categorization allows item assignment

3. **Checkpoints**
   - [ ] Checkpoint appears at question 15
   - [ ] Shows current score and accuracy
   - [ ] Provides appropriate feedback
   - [ ] Options to continue or review

4. **Results Screen**
   - [ ] Shows overall score percentage
   - [ ] Displays time taken
   - [ ] Lists weak concepts (if any)
   - [ ] Shows concept accuracy percentages

5. **Adaptive Behavior**
   - [ ] Second quiz attempt number increments
   - [ ] Questions from previously incorrect concepts appear
   - [ ] New concepts are included

## Understanding the Quiz Flow

```
┌─────────────────────────────────────────┐
│  Complete Flashcard Deck                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Click "Start Quiz" Button              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Backend Generates Adaptive Quiz        │
│  • First time: Top relevance concepts   │
│  • Later: Based on performance          │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Answer Questions 1-15                  │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Checkpoint #1                          │
│  • View score and accuracy              │
│  • Get feedback                         │
│  • Continue or review flashcards        │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Answer Questions 16-20                 │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Submit Quiz                            │
│  • Backend grades answers               │
│  • Updates performance tracking         │
│  • Identifies weak concepts             │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  View Results                           │
│  • Overall score                        │
│  • Weak concepts to review              │
│  • Option to take quiz again            │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Quiz won't generate
- **Check**: Backend is running and connected to MongoDB
- **Check**: Flashcard files exist for the course/deck
- **Check**: User ID is being set in localStorage

### Questions don't display correctly
- **Check**: Frontend console for errors
- **Check**: API response includes questions
- **Check**: Question types match what's in the flashcard JSON

### Performance not tracking
- **Check**: MongoDB connection is active
- **Check**: User ID is consistent across requests
- **Check**: Quiz submission endpoint returns successfully

### Adaptive behavior not working
- **Take multiple quizzes**: First quiz is baseline, adaptation starts from second
- **Check database**: Verify `user_deck_performance` collection has data
- **Answer some wrong**: Adaptive behavior is most obvious with incorrect answers

## Database Collections

Monitor these collections in MongoDB to verify everything is working:

1. **user_deck_performance**: Concept-level performance tracking
2. **quiz_sessions**: Active and completed quiz sessions
3. **users**: User records with total quiz attempts

### Useful MongoDB Queries

View a user's performance:
```javascript
db.user_deck_performance.findOne({user_id: "YOUR_USER_ID"})
```

View quiz sessions:
```javascript
db.quiz_sessions.find({user_id: "YOUR_USER_ID"}).sort({created_at: -1})
```

Count total quizzes taken:
```javascript
db.quiz_sessions.countDocuments({completed: true})
```

## Next Steps

Once the basic quiz is working:

1. **Customize Quiz Size**: Modify the quiz size logic in `backend/app/routers/quiz.py`
2. **Adjust Checkpoint Positions**: Update checkpoint triggers in `frontend/src/views/QuizView.jsx`
3. **Tune Weak Concept Threshold**: Change the 70% accuracy threshold in the submit endpoint
4. **Add Question Types**: Extend the question rendering in QuizView component
5. **Enhance Feedback**: Customize the checkpoint messages and results screen

## Support

For detailed implementation information, see:
- `QUIZ_ENGINE_IMPLEMENTATION.md` - Complete technical documentation
- `backend/app/routers/quiz.py` - Quiz generation and grading logic
- `frontend/src/views/QuizView.jsx` - Quiz UI components

## API Endpoints Reference

### Generate Quiz
```
POST /api/v1/quiz/generate
Headers: X-User-ID: {uuid}
Body: {
  "course_id": "MS5260",
  "deck_id": "MIS_lec_4",
  "num_questions": 20
}
```

### Submit Quiz
```
POST /api/v1/quiz/submit
Headers: X-User-ID: {uuid}
Body: {
  "quiz_id": "{quiz_uuid}",
  "course_id": "MS5260",
  "deck_id": "MIS_lec_4",
  "answers": [
    {"question_id": "{q_uuid}", "user_answer": "..."}
  ],
  "time_taken_seconds": 300
}
```

---

🎉 **Congratulations!** You now have a fully functional adaptive quiz engine that personalizes the learning experience for each user.

