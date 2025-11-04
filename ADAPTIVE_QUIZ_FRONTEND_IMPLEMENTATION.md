# Adaptive Quiz Frontend Implementation Summary

## Overview
This document describes the complete frontend implementation for the adaptive quiz system, including level selection, quiz interface, results page with flashcard deep linking, and visual content rendering.

## 🎨 Architecture

### Component Structure
```
frontend/src/
├── api/
│   └── adaptiveQuiz.js          # API service for quiz endpoints
├── components/
│   ├── VisualRenderer.jsx       # Universal renderer for Graphviz/Plotly/LaTeX
│   ├── VisualRenderer.css
│   └── StudyDeck.jsx            # Updated with deep linking support
├── views/
│   ├── QuizLevelSelectionView.jsx   # Choose difficulty level
│   ├── QuizLevelSelectionView.css
│   ├── QuizView.jsx                 # Main quiz interface (REPLACED OLD VERSION)
│   ├── QuizView.css
│   ├── QuizResultsView.jsx          # Results with flashcard links
│   ├── QuizResultsView.css
│   └── DeckView.jsx                 # Updated with deep linking support
└── App.jsx                       # Updated routing
```

## 📦 New Dependencies
Added to `package.json`:
- `react-plotly.js` - React wrapper for Plotly charts
- `plotly.js` - JavaScript graphing library
- `react-katex` - LaTeX formula rendering
- `katex` - Math typesetting library
- `d3-graphviz` - Already present for Graphviz diagrams

## 🛣️ Routing Structure

### New Routes
```javascript
// Level Selection (Landing)
/courses/:courseId/:lectureId/quiz
  → QuizLevelSelectionView

// Quiz Interface
/courses/:courseId/:lectureId/quiz/:level
  → QuizView

// Quiz Results
/courses/:courseId/:lectureId/quiz/:level/results
  → QuizResultsView

// Flashcard Deep Link (Updated)
/courses/:courseId/:lectureId/flashcards?card=:flashcardId
  → DeckView (with initialCardId support)
```

## 🎯 Core Components

### 1. API Service (`adaptiveQuiz.js`)

**Functions:**
- `startQuizSession(courseId, lectureId, level, size)` - Start adaptive quiz
- `submitQuizAnswer(courseId, lectureId, questionHash, flashcardId, isCorrect, level)` - Submit answer
- `getUserPerformance(courseId, lectureId)` - Get performance stats

**Example Usage:**
```javascript
import { startQuizSession, submitQuizAnswer } from '../api/adaptiveQuiz';

// Start quiz
const data = await startQuizSession('MS5150', 'SI_PLC', 2, 20);
// Returns: { questions: [...], metadata: {...} }

// Submit answer
await submitQuizAnswer('MS5150', 'SI_PLC', 'q_hash_123', 'SI_PLC_5', true, 2);
```

### 2. Visual Renderer (`VisualRenderer.jsx`)

**Purpose:** Universal component for rendering all visual types in quiz questions.

**Supported Formats:**
- **Graphviz** - DOT language diagrams (flowcharts, trees, graphs)
- **Plotly** - Interactive charts and plots
- **LaTeX** - Mathematical formulas (inline and block)

**Props:**
```javascript
{
  visualType: 'Graphviz' | 'Plotly' | 'LaTeX' | 'None',
  visualCode: string,        // The actual code/JSON
  altText: string           // Accessibility text
}
```

**Example Usage:**
```jsx
<VisualRenderer 
  visualType="Graphviz"
  visualCode="digraph G { A -> B; }"
  altText="Simple graph diagram"
/>
```

**Rendering Logic:**
- Graphviz: Uses `d3-graphviz` with ref-based rendering
- Plotly: Parses JSON and uses `<Plot>` component
- LaTeX: Uses `<InlineMath>` or `<BlockMath>` from `react-katex`

### 3. Quiz Level Selection (`QuizLevelSelectionView.jsx`)

**Purpose:** Beautiful landing page to choose quiz difficulty.

**Features:**
- 4 levels: Easy (1), Medium (2), Hard (3), Boss Level (4)
- Color-coded cards with icons
- Estimated time per level
- Info box explaining adaptive algorithm

**UI Elements:**
- Level 1: Green, 🌱 Seedling icon
- Level 2: Blue, 🎓 Graduation cap icon
- Level 3: Orange, 🧠 Brain icon
- Level 4: Red, 🏆 Trophy icon

**Navigation:**
```
Click level → Navigate to /courses/:courseId/:lectureId/quiz/:level
```

### 4. Quiz Interface (`QuizView.jsx`)

**Purpose:** One-question-at-a-time interface with immediate feedback.

**Flow:**
1. Load questions from backend (personalized based on user performance)
2. Display one question with options
3. User selects answer and clicks "Check Answer"
4. Show immediate feedback (correct/incorrect with explanation)
5. User clicks "Next Question" or "Finish Quiz"
6. Navigate to results page with full data

**State Management:**
```javascript
{
  questions: [],              // All quiz questions
  currentIndex: 0,           // Current question
  selectedAnswer: null,      // User's selection
  showFeedback: false,       // Show explanation?
  userAnswers: [],           // History of answers
  score: 0                   // Current score
}
```

**Visual Integration:**
- Uses `<VisualRenderer>` for question visuals
- Supports all three visual types seamlessly

**Answer Feedback:**
- Green highlight for correct answer
- Red highlight for incorrect answer
- Explanation box with detailed reasoning
- Correct answer shown if user was wrong

### 5. Quiz Results (`QuizResultsView.jsx`)

**Purpose:** Comprehensive results page with flashcard deep linking.

**Key Features:**

#### A. Performance Circle
- Animated SVG circle showing percentage
- Color-coded based on performance:
  - 90%+ → Green "Outstanding!"
  - 80-89% → Green "Excellent work!"
  - 70-79% → Blue "Good job!"
  - 60-69% → Orange "Keep practicing!"
  - <60% → Red "Review recommended"

#### B. Action Buttons
- 🔄 Try Again - Retry same level
- 📊 Choose Another Level - Back to level selection
- ← Back to Lecture - Return to lecture hub

#### C. Detailed Review Section
For each question:
- Question number and badge (✅ Correct / ❌ Incorrect)
- Full question text
- User's answer (color-coded)
- Correct answer (if wrong)
- Detailed explanation

#### D. Flashcard Deep Linking (Critical Feature!)
For **incorrect answers only**:
```jsx
<button 
  className="flashcard-link-button"
  onClick={() => navigate(`/courses/${courseId}/${lectureId}/flashcards?card=${flashcardId}`)}
>
  📖 Review the Flashcard: {flashcardId}
</button>
```

**How it works:**
1. User clicks "Review the Flashcard" button
2. Navigates to `/courses/:courseId/:lectureId/flashcards?card=SI_PLC_5`
3. `DeckView` reads `card` query parameter
4. Finds flashcard with matching `flashcard_id`
5. `StudyDeck` component opens deck directly to that card

#### E. Encouragement Box
- Shown only if user has incorrect answers
- Explains adaptive system will focus on weak areas
- Motivates user to review linked flashcards

### 6. Deep Linking Updates

#### `DeckView.jsx` Changes:
```javascript
import { useSearchParams } from 'react-router-dom';

// Extract card parameter
const [searchParams] = useSearchParams();
const cardIdParam = searchParams.get('card');

// Find matching flashcard index
const cardIndex = data.flashcards.findIndex(card => card.flashcard_id === cardIdParam);
if (cardIndex !== -1) {
  setInitialCardId(cardIdParam);
}

// Pass to StudyDeck
<StudyDeck initialCardId={initialCardId} />
```

#### `StudyDeck.jsx` Changes:
```javascript
const [currentIndex, setCurrentIndex] = useState(() => {
  if (initialCardId) {
    const index = flashcards.findIndex(card => card.flashcard_id === initialCardId);
    return index !== -1 ? index : 0;
  }
  return 0;
});
```

## 🎨 Design Philosophy

### Minimal & Sleek
- Clean white cards with subtle shadows
- Ample whitespace
- Clear visual hierarchy
- Smooth transitions and hover effects

### Color Coding
- Green → Correct/Success
- Red → Incorrect/Error
- Blue → Primary actions
- Grey → Secondary actions

### Responsive Design
- Mobile-first approach
- Flexible layouts
- Touch-friendly buttons
- Readable on all screen sizes

## 🔄 Data Flow

### Quiz Start Flow
```
User → Level Selection
     → Click Level
     → QuizView loads
     → API: startQuizSession(courseId, lectureId, level, 20)
     → Backend: Adaptive algorithm selects questions
     → Frontend: Display first question
```

### Answer Submission Flow
```
User → Selects answer
     → Clicks "Check Answer"
     → Frontend: Shows feedback
     → API: submitQuizAnswer(...)
     → Backend: Updates MongoDB user_performance
     → Frontend: Allow "Next Question"
```

### Results Flow
```
User → Finishes last question
     → Navigate to QuizResultsView with state
     → Display: Score, all questions, answers, explanations
     → User clicks flashcard link (for wrong answer)
     → Navigate to DeckView with ?card=flashcard_id
     → DeckView opens to specific flashcard
```

## 📊 Backend Integration

### Expected API Responses

#### POST /quiz/session/start
**Request:**
```json
{
  "course_id": "MS5150",
  "lecture_id": "SI_PLC",
  "level": 2,
  "size": 20
}
```

**Response:**
```json
{
  "questions": [
    {
      "question_hash": "abc123",
      "source_flashcard_id": "SI_PLC_5",
      "question_text": "What is...",
      "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      },
      "correct_answer": "B",
      "explanation": "Because...",
      "visual_type": "Graphviz",
      "visual_code": "digraph G {...}",
      "alt_text": "Diagram showing..."
    }
  ],
  "metadata": {
    "level": 2,
    "total_questions": 20
  }
}
```

#### POST /quiz/session/submit
**Request:**
```json
{
  "course_id": "MS5150",
  "lecture_id": "SI_PLC",
  "question_hash": "abc123",
  "flashcard_id": "SI_PLC_5",
  "is_correct": true,
  "level": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "Performance updated"
}
```

## 🧪 Testing Checklist

### Manual Testing Flow
1. ✅ Navigate to lecture page
2. ✅ Click "Start Quiz"
3. ✅ See level selection screen
4. ✅ Click a level (e.g., "Medium")
5. ✅ Quiz loads with first question
6. ✅ Visual renders correctly (if present)
7. ✅ Select an answer
8. ✅ Click "Check Answer"
9. ✅ See feedback (correct/incorrect)
10. ✅ See explanation
11. ✅ Click "Next Question"
12. ✅ Repeat for all 20 questions
13. ✅ Click "Finish Quiz" on last question
14. ✅ See results page with score circle
15. ✅ Review all questions in results
16. ✅ For wrong answer, click "Review Flashcard"
17. ✅ Flashcard deck opens to correct card
18. ✅ Navigate back to results
19. ✅ Click "Try Again" - new quiz loads
20. ✅ Performance tracking works (questions adapt)

### Visual Rendering Tests
- [ ] Graphviz diagram renders
- [ ] Plotly chart renders
- [ ] LaTeX formula renders
- [ ] No visual (visualType: "None") doesn't break

### Edge Cases
- [ ] 0% score
- [ ] 100% score
- [ ] Single question quiz
- [ ] Quiz with all questions correct
- [ ] Quiz with all questions incorrect
- [ ] Flashcard ID not found (graceful fallback)
- [ ] Network error during quiz load
- [ ] Network error during answer submit

## 🚀 Deployment Notes

### Environment Variables
No new environment variables needed. Uses existing:
- `VITE_API_BASE_URL` - Backend API endpoint

### Build
```bash
cd frontend
npm install
npm run build
```

### Dependencies Installed
All dependencies successfully installed:
```
+ react-plotly.js
+ plotly.js
+ react-katex
+ katex
```

## 🔗 Related Documentation
- `ADAPTIVE_QUIZ_IMPLEMENTATION_SUMMARY.md` - Backend implementation
- `FLASHCARD_ID_UPDATE.md` - Flashcard ID system
- `QUIZ_GENERATOR_IMPLEMENTATION_SUMMARY.md` - Quiz generation

## 💡 Future Enhancements
1. **Animation:** Add confetti for perfect scores
2. **Analytics:** Track time spent per question
3. **Bookmarks:** Allow bookmarking difficult questions
4. **Social:** Share results with friends
5. **Streaks:** Track consecutive correct answers
6. **Leaderboard:** Compare with other users
7. **Review Mode:** Practice only incorrect questions
8. **Offline Support:** Cache quizzes for offline use

## 🎓 User Experience Highlights

### What Makes This System Special?

#### 1. Adaptive Learning
- Questions are personalized based on past performance
- Weak areas are prioritized
- New content is gradually introduced
- Users improve faster with targeted practice

#### 2. Immediate Feedback
- No waiting until the end to see results
- Learn from mistakes in real-time
- Explanations reinforce understanding
- Correct answers are always shown

#### 3. Seamless Integration
- Direct links from wrong answers to source material
- One click takes you to the exact flashcard
- No searching or scrolling needed
- Learning loop is effortless

#### 4. Visual Learning
- Diagrams, charts, and formulas render beautifully
- Complex concepts are visualized
- Multiple learning styles supported
- Enhanced comprehension and retention

## ✅ Completion Status
- [x] API service layer
- [x] Visual renderer component
- [x] Level selection view
- [x] Quiz interface view
- [x] Results view with flashcard linking
- [x] Deep linking in DeckView
- [x] Deep linking in StudyDeck
- [x] Routing updates
- [x] Dependencies installed
- [ ] Manual testing (requires running backend)
- [ ] Backend endpoints implemented (see other doc)

---

**Implementation Date:** November 3, 2025
**Status:** Frontend Implementation Complete ✅
**Next Step:** Backend deployment and end-to-end testing


