# Personalised AI Tutor Integration Plan

## Overview
Integrate the RAG-powered chatbot as a "Personalised AI Tutor" feature in the frontend, accessible from the lecture detail page with a ChatGPT-like interface including persistent chat history.

## Current State Analysis

### Frontend
- **Route Structure**: `/courses/:courseId/:lectureId`
- **LectureDetailView**: Shows MixModeCard (premium, spans 2 columns) + 2 regular panels (Study Flashcards, Take Quiz)
- **API Pattern**: Uses `authenticatedApi.js` with Firebase auth tokens
- **API Base URL**: `VITE_API_BASE_URL` (defaults to `http://localhost:8000`)
- **Design System**: Brand green (#2d7a3e), modern cards with hover effects, responsive grid

### Backend (RAG Pipeline)
- **Port**: 8001 (Config.API_PORT)
- **Endpoints**:
  - `POST /chat/{course_id}` - Send message
  - `POST /chat/{course_id}/clear` - Clear session
  - `GET /chat/{course_id}/history` - Get history
- **Storage**: In-memory (`ConversationManager.sessions` dict)
- **Session ID**: String (defaults to "default")
- **No user authentication**: Currently accepts any session_id

## Implementation Plan

### Phase 1: Frontend UI Components

#### 1.1 Create TutorCard Component
**File**: `frontend/src/components/Tutor/TutorCard.jsx`
- Similar structure to `MixModeCard.jsx`
- Icon: Brain/Sparkles (use `FaBrain` or `FaSparkles` from react-icons)
- Title: "Personalised AI Tutor"
- Tagline: "Intelligent Learning Assistant"
- Description: "Get instant, personalized explanations for any concept. Ask questions in natural language and receive answers based on your course materials."
- Features:
  - "Context-Aware"
  - "24/7 Available"
  - "Multi-Perspective"
- Button: "Start Chatting →"
- Styling: Match MixModeCard but with distinct color (maybe purple/blue gradient or keep green)

#### 1.2 Update LectureDetailView
**File**: `frontend/src/views/LectureDetailView.jsx`
- Add TutorCard to `action-panels` grid
- Layout options:
  - **Option A**: TutorCard spans 2 columns (like MixModeCard), placed first
  - **Option B**: TutorCard as regular panel (1 column), placed alongside others
- Add `handleTutorClick` handler that navigates to `/courses/${courseId}/${lectureId}/tutor`
- Import TutorCard component

#### 1.3 Create TutorChatView Component
**File**: `frontend/src/views/TutorChatView.jsx`
- **Layout**: Split view (sidebar + main chat)
  - **Sidebar** (left, ~300px width):
    - Header: "Conversations" + "New Chat" button
    - List of past conversations (scrollable)
    - Each item: Title (first message or "New Chat"), timestamp, delete button
    - Click to switch conversations
  - **Main Chat** (right, flex):
    - Header: Course name + lecture name + "Clear Chat" button
    - Chat messages area (scrollable)
    - Input area: Text input + Send button
- **State Management**:
  - `conversations`: Array of conversation objects `{id, title, messages, createdAt, updatedAt}`
  - `activeConversationId`: Current conversation ID
  - `inputMessage`: Current input text
  - `isLoading`: Loading state for API calls
- **Features**:
  - Auto-scroll to bottom on new message
  - Loading indicator while waiting for response
  - Error handling with user-friendly messages
  - Markdown rendering for responses (if needed)
- **Styling**: Match existing design system (green theme, modern cards)

#### 1.4 Create TutorCard CSS
**File**: `frontend/src/components/Tutor/TutorCard.css`
- Similar to `MixModeCard.css`
- Distinct styling to differentiate from MixModeCard

#### 1.5 Create TutorChatView CSS
**File**: `frontend/src/views/TutorChatView.css`
- Sidebar styling
- Chat message bubbles (user vs assistant)
- Input area styling
- Responsive design (mobile: hide sidebar, show toggle)

### Phase 2: API Integration

#### 2.1 Create Tutor API Service
**File**: `frontend/src/api/tutorChat.js`
- Pattern: Similar to `mixMode.js`
- Functions:
  - `sendMessage(courseId, message, sessionId)` → POST to RAG backend
  - `getChatHistory(courseId, sessionId)` → GET history
  - `clearChat(courseId, sessionId)` → POST clear
  - `listConversations(courseId, userId)` → GET all sessions (new endpoint needed)
- **Important**: Use different API base URL for RAG backend
  - Option A: Add `VITE_RAG_API_BASE_URL` env var (defaults to `http://localhost:8001`)
  - Option B: Proxy through main backend (recommended for production)
- **Session ID Strategy**:
  - Generate unique session ID per conversation: `userId_courseId_lectureId_timestamp`
  - Store in localStorage for persistence
  - Use Firebase UID for user identification

#### 2.2 Update authenticatedApi.js (if needed)
- Add support for different base URLs
- Or create separate `ragApi.js` for RAG backend calls

### Phase 3: Backend Enhancements

#### 3.1 Add Session Listing Endpoint
**File**: `backend/image_rag_pipeline/app/api/server.py`
- New endpoint: `GET /chat/{course_id}/sessions?user_id={user_id}`
- Returns list of all sessions for a user in a course
- Response format:
  ```json
  {
    "sessions": [
      {
        "session_id": "user123_MS5260_lec1_1234567890",
        "title": "What is MIS?",
        "message_count": 4,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:05:00Z"
      }
    ]
  }
  ```

#### 3.2 Enhance Session Management
- **Session ID Format**: `{user_id}_{course_id}_{lecture_id}_{timestamp}`
- **Session Metadata**: Store title (first message), timestamps, message count
- **Storage**: For MVP, keep in-memory but structure for future DB migration
- **User Context**: Accept `user_id` in request headers (from Firebase token)

#### 3.3 Add Authentication (Optional for MVP)
- Extract user_id from Firebase token in request headers
- Validate token (can be done in middleware)
- Associate sessions with user_id

### Phase 4: Route Integration

#### 4.1 Add Route to App.jsx
**File**: `frontend/src/App.jsx`
- Add route: `/courses/:courseId/:lectureId/tutor`
- Place under nested course routes (same level as `/flashcards`, `/quiz`, `/mix`)
- Wrap in `ProtectedRoute` (requires authentication)

### Phase 5: Polish & Testing

#### 5.1 Error Handling
- Network errors
- API errors
- Empty states (no conversations)
- Loading states

#### 5.2 Analytics
- Track: "Started Tutor Chat", "Sent Message", "Switched Conversation"
- Use existing `trackEvent` from `amplitude.js`

#### 5.3 Responsive Design
- Mobile: Hide sidebar, show hamburger menu
- Tablet: Collapsible sidebar
- Desktop: Full split view

## Technical Decisions

### Session ID Strategy
- **Format**: `{firebase_uid}_{course_id}_{lecture_id}_{timestamp}`
- **Storage**: localStorage for frontend persistence
- **Backend**: Store in `ConversationManager.sessions` with metadata

### API Base URL
- **Development**: Use `VITE_RAG_API_BASE_URL=http://localhost:8001`
- **Production**: Proxy through main backend at `/api/rag/*` → RAG backend

### Conversation Title
- Use first user message (truncated to 50 chars)
- Or generate from first exchange using LLM (future enhancement)

### Message Format
- User messages: `{role: 'user', content: string, timestamp: Date}`
- Assistant messages: `{role: 'assistant', content: string, timestamp: Date}`

## File Structure

```
frontend/src/
├── components/
│   └── Tutor/
│       ├── TutorCard.jsx
│       └── TutorCard.css
├── views/
│   ├── LectureDetailView.jsx (updated)
│   ├── TutorChatView.jsx (new)
│   └── TutorChatView.css (new)
├── api/
│   └── tutorChat.js (new)
└── utils/
    └── ragApi.js (new, optional)

backend/image_rag_pipeline/app/api/
└── server.py (updated with new endpoints)
```

## Environment Variables

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000  # Main backend
VITE_RAG_API_BASE_URL=http://localhost:8001  # RAG backend
```

### Backend (.env in image_rag_pipeline)
```bash
# Already exists, no changes needed
```

## Testing Checklist

- [ ] TutorCard appears on LectureDetailView
- [ ] Clicking TutorCard navigates to chat view
- [ ] Can send messages and receive responses
- [ ] Chat history persists in sidebar
- [ ] Can create new conversations
- [ ] Can switch between conversations
- [ ] Can clear/delete conversations
- [ ] Responsive design works on mobile
- [ ] Error handling works (network errors, API errors)
- [ ] Loading states display correctly
- [ ] Analytics events fire correctly

## Future Enhancements (Post-MVP)

1. **Database Persistence**: Store conversations in Firebase/PostgreSQL
2. **Conversation Search**: Search past conversations
3. **Export Conversations**: Download chat history as PDF/text
4. **Conversation Sharing**: Share conversations with others
5. **Voice Input**: Speech-to-text for questions
6. **Image Upload**: Ask questions about uploaded images
7. **Conversation Title Generation**: Use LLM to generate better titles
8. **Multi-turn Context**: Improve context window management
9. **Rate Limiting**: Prevent abuse
10. **Conversation Analytics**: Track most asked questions, topics

## Implementation Order

1. ✅ Create TutorCard component
2. ✅ Add TutorCard to LectureDetailView
3. ✅ Create TutorChatView component (basic, no sidebar)
4. ✅ Create API service
5. ✅ Add route
6. ✅ Test basic chat flow
7. ✅ Add sidebar with conversation list
8. ✅ Add backend session listing endpoint
9. ✅ Polish styling and UX
10. ✅ Add error handling and loading states
11. ✅ Test responsive design
12. ✅ Add analytics

