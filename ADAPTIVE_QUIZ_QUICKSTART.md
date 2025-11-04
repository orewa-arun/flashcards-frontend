# Adaptive Quiz System - Quick Start Guide

## 🎯 What's Been Built

A complete adaptive quiz system with:
- ✅ **Backend**: MongoDB-based performance tracking with adaptive question selection
- ✅ **Frontend**: Beautiful UI with level selection, quiz interface, and results
- ✅ **Deep Linking**: Wrong answers link directly to source flashcards
- ✅ **Visual Support**: Graphviz, Plotly, and LaTeX rendering in questions

## 🚀 Getting Started

### 1. Start the Backend

```bash
cd backend
python3 -m uvicorn app.main:app --reload --port 8000
```

**Important:** Make sure MongoDB is running and configured in your environment.

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend will start at `http://localhost:5173`

### 3. Test the Flow

1. **Login** to the application
2. Navigate to a course (e.g., MS5150)
3. Select a lecture (e.g., SI_PLC)
4. Click **"Start Quiz"** button
5. Choose a difficulty level:
   - 🌱 Easy (Level 1)
   - 🎓 Medium (Level 2)
   - 🧠 Hard (Level 3)
   - 🏆 Boss Level (Level 4)
6. Answer questions one by one
7. Get immediate feedback after each answer
8. Review results and click flashcard links for wrong answers

## 📁 Key Files Created

### Backend
```
backend/app/
├── models/
│   └── user_performance.py          # MongoDB schema for tracking
├── services/
│   ├── user_performance_service.py   # Database operations
│   └── adaptive_quiz_service.py      # Adaptive algorithm
└── routers/
    └── adaptive_quiz.py              # API endpoints
```

### Frontend
```
frontend/src/
├── api/
│   └── adaptiveQuiz.js               # API client
├── components/
│   └── VisualRenderer.jsx            # Graphviz/Plotly/LaTeX renderer
└── views/
    ├── QuizLevelSelectionView.jsx    # Level selection screen
    ├── QuizView.jsx                  # Quiz interface (REPLACED OLD)
    └── QuizResultsView.jsx           # Results with flashcard links
```

## 🔄 How the Adaptive System Works

### First Quiz (Cold Start)
- Questions are randomly selected from the lecture's quiz JSON files
- Level determines which `level_*_quiz.json` file is used
- All 20 questions are treated equally (no performance data yet)

### Subsequent Quizzes (Adaptive Mode)
- System calculates "weakness scores" for each flashcard:
  ```
  weakness_score = (incorrect_count / total_attempts) 
                 + freshness_bonus (for never-seen flashcards)
  ```
- Questions from "weak" flashcards are prioritized
- Uses weighted random sampling (not purely deterministic)
- New content is gradually introduced with freshness bonus

### After Each Answer
- Performance data is updated in MongoDB:
  ```javascript
  {
    user_id: "...",
    course_id: "MS5150",
    lecture_id: "SI_PLC",
    flashcard_performance: {
      "SI_PLC_5": { correct: 3, incorrect: 1, last_attempted: "..." }
    },
    question_performance: {
      "q_hash_123": { correct: 1, incorrect: 0, last_attempted: "..." }
    }
  }
  ```

## 🎯 API Endpoints

### Start Quiz Session
```
POST /quiz/session/start
Body: {
  "course_id": "MS5150",
  "lecture_id": "SI_PLC",
  "level": 2,
  "size": 20
}
Response: {
  "questions": [...],
  "metadata": {...}
}
```

### Submit Answer
```
POST /quiz/session/submit
Body: {
  "course_id": "MS5150",
  "lecture_id": "SI_PLC",
  "question_hash": "abc123",
  "flashcard_id": "SI_PLC_5",
  "is_correct": true,
  "level": 2
}
Response: {
  "success": true
}
```

## 🧪 Testing Scenarios

### Scenario 1: New User (Cold Start)
1. Start quiz (Level 2)
2. Answer 10 questions correctly, 10 incorrectly
3. Submit quiz
4. Start another quiz at same level
5. **Expected:** Questions from missed flashcards appear more frequently

### Scenario 2: Flashcard Deep Linking
1. Complete quiz with some wrong answers
2. On results page, click "Review the Flashcard" for a wrong answer
3. **Expected:** Flashcard deck opens to exact card (e.g., SI_PLC_5)

### Scenario 3: Visual Rendering
1. Find a question with `visual_type: "Graphviz"`
2. **Expected:** Diagram renders correctly
3. Try questions with Plotly and LaTeX
4. **Expected:** All visuals display properly

### Scenario 4: Level Progression
1. Start with Easy (Level 1)
2. Get 90%+ score
3. Try Medium (Level 2)
4. **Expected:** Questions are noticeably harder

## 🐛 Troubleshooting

### Backend Issues

**MongoDB Connection Error:**
```bash
# Check MongoDB is running
mongosh

# Verify connection string in backend/.env or backend/app/config.py
```

**Import Errors:**
```bash
cd backend
pip install -r requirements.txt
```

**Quiz Questions Not Loading:**
- Verify quiz JSON files exist: `backend/courses/{course_id}/quiz/{lecture_id}_level_*_quiz.json`
- If missing, run the quiz generator

### Frontend Issues

**Dependencies Not Found:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Visuals Not Rendering:**
- Check browser console for errors
- Verify `d3-graphviz`, `react-plotly.js`, `react-katex` are installed
- Look for JSON parsing errors in Plotly data

**Deep Linking Not Working:**
- Verify flashcards have `flashcard_id` field
- Check that `*_cognitive_flashcards_only.json` files exist
- Ensure `flashcard_id` matches between quiz questions and flashcards

## 📊 Data Files Required

### For Each Lecture:
```
backend/courses/MS5150/
├── cognitive_flashcards/
│   └── SI_PLC/
│       └── SI_PLC_cognitive_flashcards_only.json  # With flashcard_id
└── quiz/
    ├── SI_PLC_level_1_quiz.json                   # Easy questions
    ├── SI_PLC_level_2_quiz.json                   # Medium questions
    ├── SI_PLC_level_3_quiz.json                   # Hard questions
    └── SI_PLC_level_4_quiz.json                   # Boss level questions
```

### Frontend Public Files:
```
frontend/public/courses/MS5150/
└── cognitive_flashcards/
    └── SI_PLC/
        └── SI_PLC_cognitive_flashcards_only.json  # Same as backend
```

## 🔧 Configuration

### Backend Environment
```bash
# backend/.env or backend/app/config.py
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=self_learning_ai
COLLECTION_USER_PERFORMANCE=user_performance
```

### Frontend Environment
```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

## 📈 Performance Optimization

### Backend
- MongoDB indexes on `user_id`, `course_id`, `lecture_id`
- Atomic updates using `$inc` operator
- Efficient weighted sampling algorithm

### Frontend
- Component memoization for visual renderers
- Lazy loading of quiz questions
- Optimistic UI updates for answer submission

## 🎓 User Flow Diagram

```
Login → Course List → Course Detail → Lecture Detail
                                          ↓
                                    [Flashcards] or [Quiz]
                                          ↓
                                    Quiz Level Selection
                                          ↓
                                    Quiz Interface (Q1)
                                          ↓
                                    [Answer] → [Feedback]
                                          ↓
                                    Quiz Interface (Q2)
                                          ↓
                                         ...
                                          ↓
                                    Quiz Results
                                          ↓
                            [Wrong Answer] → [Review Flashcard]
                                                      ↓
                                                Flashcard Deck (Specific Card)
```

## 🎉 Success Criteria

Your system is working correctly if:
- ✅ Quiz loads with 20 personalized questions
- ✅ Visual content (diagrams, charts, formulas) renders
- ✅ Immediate feedback shows after each answer
- ✅ Results page displays all questions with explanations
- ✅ Clicking flashcard link opens deck to correct card
- ✅ Subsequent quizzes show different questions (adaptive)
- ✅ Performance data is saved in MongoDB

## 📚 Next Steps

1. **Test with Real Users:** Gather feedback on difficulty levels
2. **Analyze Performance Data:** See which flashcards are weakest
3. **Generate More Questions:** Add more questions per flashcard
4. **Add Analytics:** Track user learning curves
5. **Mobile Testing:** Ensure responsive design works
6. **Deploy:** Push to production (Vercel + Railway/Render)

## 🆘 Need Help?

### Common Questions

**Q: How do I generate quiz questions?**
A: See `QUIZ_GENERATION_GUIDE.md` and `generate_quizzes.py`

**Q: How do I add flashcard_id to existing flashcards?**
A: See `FLASHCARD_ID_UPDATE.md`

**Q: Where is the adaptive algorithm?**
A: `backend/app/services/adaptive_quiz_service.py`

**Q: How does MongoDB tracking work?**
A: See `ADAPTIVE_QUIZ_IMPLEMENTATION_SUMMARY.md`

### Documentation
- `ADAPTIVE_QUIZ_FRONTEND_IMPLEMENTATION.md` - Frontend details
- `ADAPTIVE_QUIZ_IMPLEMENTATION_SUMMARY.md` - Backend details
- `QUIZ_GENERATION_GUIDE.md` - Quiz generation process
- `FLASHCARD_ID_UPDATE.md` - Flashcard ID system

---

**Ready to test?** Start both backend and frontend, then navigate to a lecture and click "Start Quiz"! 🚀


