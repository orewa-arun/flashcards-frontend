# ChatGPT-Style Conversation History Implementation

## Overview

Successfully implemented a ChatGPT-style conversation management system for the AI Tutor feature. The system now stores all conversations permanently in the database and displays them in a sidebar for easy access.

## What Was Implemented

### Backend (Python/FastAPI)

#### 1. Database Schema
Created two new MongoDB collections:

**`tutor_conversations`** - Stores conversation metadata
- `conversation_id`: Unique identifier
- `user_id`: Firebase UID of the user
- `course_id`: Course identifier
- `lecture_id`: Lecture identifier
- `title`: Auto-generated from first message
- `created_at`: Timestamp
- `updated_at`: Last message timestamp
- `message_count`: Number of messages

**`tutor_messages`** - Stores all messages
- `conversation_id`: Links to conversation
- `role`: 'user' or 'assistant'
- `content`: Message text
- `timestamp`: When sent

#### 2. New Backend Files

**`backend/app/models/conversation.py`**
- Pydantic models for conversations and messages
- Request/response models for API endpoints

**`backend/app/services/conversation_service.py`**
- Business logic for conversation management
- CRUD operations for conversations and messages
- Methods to integrate with RAG backend

**`backend/app/routers/conversations.py`**
- RESTful API endpoints for conversation management
- Bridges between frontend and RAG backend

#### 3. API Endpoints

All endpoints require authentication (Bearer token):

- `POST /api/tutor/conversations` - Create new conversation
- `GET /api/tutor/conversations` - List all user conversations (filterable by course/lecture)
- `GET /api/tutor/conversations/{id}` - Get conversation with all messages
- `POST /api/tutor/conversations/{id}/messages` - Send message and get AI response
- `DELETE /api/tutor/conversations/{id}` - Delete conversation
- `PATCH /api/tutor/conversations/{id}/title` - Update conversation title

#### 4. Integration Updates

**`backend/app/main.py`**
- Registered new conversations router

**`backend/app/database_indexes.py`**
- Added indexes for optimal query performance

### Frontend (React)

#### 1. New Components

**`frontend/src/components/Tutor/ConversationSidebar.jsx`**
- ChatGPT-style sidebar with conversation list
- "New Chat" button
- Delete conversation functionality
- Shows conversation titles and timestamps
- Highlights active conversation

**`frontend/src/components/Tutor/ConversationSidebar.css`**
- Dark theme styling matching ChatGPT aesthetic
- Responsive design (mobile-ready)
- Smooth animations and hover effects

#### 2. Updated Files

**`frontend/src/api/tutorApi.js`**
- Complete rewrite to use new backend API
- Functions for all conversation operations
- Proper authentication with Firebase tokens

**`frontend/src/views/TutorChatView.jsx`**
- Refactored to support conversation management
- Integrated sidebar component
- Auto-creates conversations on first message
- Loads conversation history when selected
- Updates title automatically from first message

**`frontend/src/views/TutorChatView.css`**
- Updated layout to support sidebar
- Flexbox container for side-by-side layout
- Full-height viewport design

**`frontend/src/App.jsx`**
- Added route for specific conversation: `/courses/:courseId/:lectureId/tutor/:conversationId`
- Supports both with and without conversationId

## How It Works

### User Flow

1. **Initial Load**
   - User navigates to AI Tutor for a lecture
   - Sidebar loads all previous conversations for that lecture
   - Main area shows welcome screen with example questions

2. **Starting New Chat**
   - User clicks "New Chat" button
   - Creates empty conversation in database
   - Navigates to new conversation URL
   - Ready to send first message

3. **Sending Messages**
   - User types message and sends
   - Frontend saves user message to database
   - Backend calls RAG API to get AI response
   - AI response saved to database
   - First message auto-generates conversation title
   - Sidebar updates to show new title and timestamp

4. **Switching Conversations**
   - Click any conversation in sidebar
   - Loads all messages from database
   - URL updates to include conversation ID
   - Messages appear in chat area

5. **Deleting Conversations**
   - Hover over conversation, click trash icon
   - Confirms deletion
   - Removes conversation and all messages from database
   - If deleted conversation was active, returns to welcome screen

## Technical Details

### Authentication Flow
1. Frontend gets Firebase ID token from current user
2. Token sent in `Authorization: Bearer <token>` header
3. Backend validates token using Firebase Admin SDK
4. User ID extracted for database queries

### Data Flow
```
User Input → Frontend
  ↓
Create/Get Conversation ID
  ↓
Save User Message → MongoDB
  ↓
Call RAG Backend (port 8001)
  ↓
Get AI Response
  ↓
Save AI Message → MongoDB
  ↓
Update Conversation Metadata
  ↓
Display to User
```

### URL Structure
- No conversation: `/courses/MS5260/MIS_lec_1-3/tutor`
- With conversation: `/courses/MS5260/MIS_lec_1-3/tutor/abc123-def456-...`

### Auto-Title Generation
- When first message sent in conversation
- Uses first 50 characters of user's message
- Appends "..." if truncated
- Updates conversation title in database and sidebar

## Key Features

✅ **Persistent Storage** - All conversations saved permanently
✅ **ChatGPT-Style UI** - Clean, dark-themed sidebar
✅ **Real-time Updates** - Sidebar refreshes after actions
✅ **Auto-Titles** - Generated from first message
✅ **Delete Protection** - Confirmation dialog before deletion
✅ **Mobile Ready** - Responsive design for small screens
✅ **Authenticated** - All requests require user login
✅ **Fast Queries** - Optimized database indexes
✅ **Empty States** - Helpful UI when no conversations exist

## Testing Checklist

- [x] Create new conversation
- [x] Send messages in conversation
- [x] Load existing conversation
- [x] Switch between conversations
- [x] Delete conversation
- [x] Auto-title generation
- [x] Sidebar updates after actions
- [x] Empty state displays correctly
- [x] Authentication required
- [x] Mobile responsiveness

## Next Steps (Future Enhancements)

1. **Search Conversations** - Add search bar to sidebar
2. **Rename Conversations** - Allow manual title editing
3. **Export Conversations** - Download as PDF/text
4. **Conversation Tags** - Organize by topic
5. **Archive Conversations** - Hide without deleting
6. **Keyboard Shortcuts** - Quick navigation (Cmd+K)
7. **Share Conversations** - Generate shareable links
8. **Conversation Notes** - Side panel with AI-generated summaries

## Configuration

### Environment Variables

Backend (`backend/.env`):
```
MONGODB_URL=your_mongodb_connection_string
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
```

Frontend (`frontend/.env`):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
```

## Running the System

### Start Backend (Terminal 1)
```bash
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
uvicorn app.main:app --reload --port 8000
```

### Start RAG Backend (Terminal 2)
```bash
cd backend/image_rag_pipeline
source venv/bin/activate
uvicorn app.api.server:app --reload --port 8001
```

### Start Frontend (Terminal 3)
```bash
cd frontend
npm run dev
```

## Database Indexes Created

For optimal performance, the following indexes are automatically created on startup:

**tutor_conversations:**
- `conversation_id` (unique)
- `user_id + updated_at` (sorted list)
- `user_id + course_id + lecture_id` (filtering)

**tutor_messages:**
- `conversation_id + timestamp` (chronological order)

## API Response Examples

### List Conversations
```json
[
  {
    "conversation_id": "abc-123",
    "title": "What is competitive advantage?",
    "course_id": "MS5260",
    "lecture_id": "MIS_lec_1-3",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:35:00Z",
    "message_count": 4
  }
]
```

### Get Conversation
```json
{
  "conversation_id": "abc-123",
  "title": "What is competitive advantage?",
  "course_id": "MS5260",
  "lecture_id": "MIS_lec_1-3",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "messages": [
    {
      "role": "user",
      "content": "What is competitive advantage?",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Competitive advantage refers to...",
      "timestamp": "2025-01-15T10:30:15Z"
    }
  ]
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│  ┌──────────────────┐  ┌───────────────────────────┐   │
│  │ ConversationList │  │   TutorChatView           │   │
│  │    Sidebar       │  │   (Main Chat Area)        │   │
│  └──────────────────┘  └───────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ (HTTP + Auth Token)
┌─────────────────────────────────────────────────────────┐
│                Backend API (Port 8000)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  /api/tutor/conversations (CRUD Endpoints)       │  │
│  └──────────────────────────────────────────────────┘  │
│                            │                             │
│         ┌──────────────────┼──────────────────┐         │
│         ▼                  ▼                  ▼         │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │MongoDB   │      │Firebase  │      │RAG API   │     │
│  │(Messages)│      │(Auth)    │      │(Port 8001)│    │
│  └──────────┘      └──────────┘      └──────────┘     │
└─────────────────────────────────────────────────────────┘
```

## Success! 🎉

The AI Tutor now has a robust, ChatGPT-style conversation management system with:
- ✅ Permanent storage of all conversations
- ✅ Beautiful, intuitive UI
- ✅ Fast, optimized queries
- ✅ Secure, authenticated access
- ✅ Mobile-responsive design

All conversations are now safely stored and easily accessible!

