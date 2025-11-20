# AI Tutor Setup Guide

## Overview
The AI Tutor feature has been successfully integrated into the frontend. This guide will help you set it up and test it.

## What's Been Implemented

### Frontend Components
1. **TutorCard** (`frontend/src/components/Tutor/TutorCard.jsx`)
   - Premium card displayed on the LectureDetailView
   - Purple/indigo theme to differentiate from Mix Mode (green)
   - Click to navigate to chat interface

2. **TutorChatView** (`frontend/src/views/TutorChatView.jsx`)
   - Full-page chat interface
   - Persistent chat history per lecture
   - Auto-scroll, typing indicators, error handling
   - Example questions for first-time users

3. **API Service** (`frontend/src/api/tutorApi.js`)
   - Communicates with RAG backend on port 8001
   - Session management with format: `{firebase_uid}_{course_id}_{lecture_id}`
   - Functions: sendMessage, getChatHistory, clearChat

### Routes
- Added route: `/courses/:courseId/:lectureId/tutor`
- Protected with authentication (requires login)

## Setup Instructions

### 1. Environment Variables

Add this to your `frontend/.env` file (or create it if it doesn't exist):

```bash
# Main Backend API (Flask/FastAPI)
VITE_API_BASE_URL=http://localhost:8000

# RAG Backend API (Image-RAG Pipeline) - NEW!
VITE_RAG_API_BASE_URL=http://localhost:8001

# Your existing Firebase and Amplitude configs...
```

### 2. Start the RAG Backend

The AI Tutor needs the RAG backend running on port 8001.

```bash
# Navigate to the RAG backend directory
cd backend/image_rag_pipeline

# Activate your Python virtual environment
source ../../.venv/bin/activate  # or wherever your venv is

# Make sure you have the GOOGLE_API_KEY set
export GOOGLE_API_KEY='your-gemini-api-key'

# Start the server
python -m app.api.server
```

The server should start on `http://localhost:8001`.

### 3. Start the Frontend

```bash
# In a new terminal, navigate to frontend
cd frontend

# Start the dev server
npm run dev
```

The frontend should start on `http://localhost:5173`.

### 4. Test the Integration

1. **Navigate to a lecture**:
   - Go to http://localhost:5173
   - Log in (if not already)
   - Select a course (e.g., MS5260)
   - Select a lecture (e.g., MIS_lec_1-3)

2. **You should see**:
   - The existing Mix Mode card (green, spans 2 columns)
   - **NEW**: The AI Tutor card (purple/indigo, regular size)
   - Study Flashcards panel
   - Take Quiz panel

3. **Click on "AI Tutor"**:
   - Should navigate to `/courses/MS5260/MIS_lec_1-3/tutor`
   - You'll see a chat interface with:
     - Header with breadcrumb navigation
     - Welcome message with example questions
     - Input box at the bottom

4. **Test the chat**:
   - Click on an example question OR type your own
   - Press Enter or click the send button
   - You should see:
     - Your message (green bubble, right side)
     - Typing indicator (three dots)
     - AI response (white bubble, left side)

5. **Test persistence**:
   - Navigate away (back to lecture detail)
   - Click AI Tutor again
   - Your previous conversation should still be there!

6. **Test clear chat**:
   - Click "Clear Chat" button in the header
   - Confirm the dialog
   - Chat should be cleared

## Troubleshooting

### Issue: "Failed to initialize chat"
- **Cause**: Not logged in or Firebase auth issue
- **Solution**: Make sure you're logged in with a valid Firebase account

### Issue: "Failed to get response"
- **Cause**: RAG backend not running or wrong URL
- **Solution**: 
  - Check that RAG backend is running on port 8001
  - Check `VITE_RAG_API_BASE_URL` in your `.env`
  - Check browser console for network errors

### Issue: TutorCard not showing
- **Cause**: Frontend not rebuilt after changes
- **Solution**: 
  - Stop the dev server (Ctrl+C)
  - Run `npm run dev` again
  - Hard refresh the browser (Cmd+Shift+R or Ctrl+Shift+R)

### Issue: CORS errors
- **Cause**: RAG backend not allowing frontend origin
- **Solution**: The RAG backend should already have CORS enabled. If not, check `app/api/server.py` for CORS middleware.

## Features Implemented (Phase 1 MVP)

✅ TutorCard component on LectureDetailView
✅ Full chat interface with message history
✅ Persistent chat per lecture (using session IDs)
✅ Auto-scroll to latest message
✅ Typing indicator while waiting for response
✅ Error handling with user-friendly messages
✅ Example questions for first-time users
✅ Clear chat functionality
✅ Responsive design (mobile-friendly)
✅ Analytics tracking (Amplitude events)
✅ Protected route (requires authentication)

## What's NOT Implemented (Future - Phase 2)

❌ Multiple conversations per lecture (sidebar with conversation list)
❌ Persistent storage (currently in-memory, lost on server restart)
❌ Conversation titles (auto-generated from first message)
❌ Delete individual conversations
❌ Search conversations
❌ Export conversations
❌ Markdown rendering in responses
❌ Code syntax highlighting
❌ Image upload support

## Next Steps

Once you've tested and confirmed everything works:

1. **Phase 2 Planning**: Decide if you want to implement the full ChatGPT-like interface with:
   - Sidebar with multiple conversations
   - File-based persistence
   - Conversation management (rename, delete, search)

2. **Production Deployment**:
   - Set up proper environment variables
   - Consider proxying RAG backend through main backend
   - Set up persistent storage (database or file system)

3. **Enhancements**:
   - Better markdown rendering
   - Code syntax highlighting
   - Copy response button
   - Rate limiting
   - Usage analytics

## File Structure

```
frontend/src/
├── components/
│   └── Tutor/
│       ├── TutorCard.jsx          ✅ NEW
│       └── TutorCard.css          ✅ NEW
├── views/
│   ├── LectureDetailView.jsx     ✅ UPDATED
│   ├── TutorChatView.jsx         ✅ NEW
│   └── TutorChatView.css         ✅ NEW
├── api/
│   └── tutorApi.js                ✅ NEW
└── App.jsx                        ✅ UPDATED (new route)

backend/image_rag_pipeline/
└── app/api/
    └── server.py                  ✅ EXISTING (no changes needed)
```

## Support

If you encounter any issues:
1. Check the browser console for errors
2. Check the RAG backend logs
3. Verify environment variables are set correctly
4. Make sure you're logged in with Firebase auth
5. Try clearing browser cache and hard refresh

Happy tutoring! 🎓🤖

