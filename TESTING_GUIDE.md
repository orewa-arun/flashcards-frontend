# Testing Guide: Admin Upload Page

Complete step-by-step guide to run and test the new `/admin/upload` page.

---

## Prerequisites

- **Python 3.8+** installed
- **Node.js 16+** and **npm/yarn** installed
- **PostgreSQL** installed and running
- **Cloudflare R2** account (for PDF storage)
- **API Keys**: Gemini, Anthropic (Claude), and optionally OpenAI

---

## Part 1: Backend Setup

### Step 1: Install PostgreSQL (if not already installed)

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

### Step 2: Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE self_learning_ai;

# Exit psql
\q
```

Or using command line:
```bash
createdb -U postgres self_learning_ai
```

### Step 3: Navigate to Backend Directory

```bash
cd backend
```

### Step 4: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Copy from example
cp env.example .env

# Edit .env file with your values
nano .env  # or use your preferred editor
```

**Required `.env` variables:**

```bash
# PostgreSQL Configuration
POSTGRES_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/self_learning_ai

# Replace 'your_password' with your actual PostgreSQL password
# Replace 'self_learning_ai' if you used a different database name

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Origins (for frontend)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# AI API Keys (REQUIRED)
GEMINI_API_KEY=your_actual_gemini_api_key
ANTHROPIC_API_KEY=your_actual_anthropic_api_key
OPENAI_API_KEY=your_actual_openai_api_key  # Optional

# AI Model Configuration
MODEL_ANALYSIS=gemini-2.0-flash-exp
MODEL_FLASHCARDS=claude-3-haiku-20240307
MODEL_QUIZ=gemini-2.0-flash-exp

# Cloudflare R2 Configuration (REQUIRED for PDF uploads)
CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_key
CLOUDFLARE_R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=course-content

# MongoDB (for existing analytics - keep if you have it)
MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=study_analytics
```

### Step 7: Start Backend Server

```bash
# Make sure you're in the backend directory with venv activated
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     PostgreSQL connection pool created successfully
INFO:     Database tables created/verified successfully
INFO:     Application startup complete.
```

**Verify backend is running:**
- Open browser: http://localhost:8000/docs
- You should see the FastAPI Swagger documentation
- Check http://localhost:8000/health - should return `{"status": "healthy"}`

---

## Part 2: Frontend Setup

### Step 1: Navigate to Frontend Directory

Open a **new terminal window** (keep backend running):

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Configure Frontend Environment

Create or check `.env` file in `frontend/` directory:

```bash
# Create .env file if it doesn't exist
touch .env
```

Add/verify these variables:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000

# Firebase Configuration (if you have it)
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
# ... other Firebase config
```

### Step 4: Start Frontend Development Server

```bash
npm run dev
```

**Expected output:**
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Verify frontend is running:**
- Open browser: http://localhost:5173
- You should see the landing page

---

## Part 3: Testing the Admin Upload Page

### Step 1: Access the Admin Upload Page

1. **Make sure you're logged in** to the application
   - If not logged in, the protected route will redirect you to login

2. **Navigate directly to:**
   ```
   http://localhost:5173/admin/upload
   ```

   ⚠️ **Note:** This is a hidden route (no navigation link), so you must type it directly in the browser.

### Step 2: Test Content Ingestion

1. **Fill out the upload form:**
   - **Course Code**: `MAPP_F_MKT404_EN_2025` (or any format you prefer)
   - **Course Name**: `Marketing Analytics` (or any name)
   - **Instructor**: `Dr. John Smith` (optional)
   - **Reference Textbooks**: `Book 1, Book 2` (comma-separated, optional)
   - **Additional Info**: Any notes (optional)

2. **Select PDF files:**
   - Click the file input area
   - Select one or more PDF files from your computer
   - Files should appear in the list

3. **Click "Upload & Ingest"**
   - You should see a loading spinner
   - On success, you'll see a green success message
   - The form will reset
   - The lecture list below should automatically refresh

### Step 3: Test Pipeline Actions

After uploading, you should see lectures in the **Content Pipeline** section:

1. **View Lecture Status:**
   - Each lecture shows status dots for: Analysis, Flashcards, Quiz, Indexing
   - Click on a lecture card to expand and see details

2. **Test Analysis Stage:**
   - Click the **"Run"** button next to "Analysis"
   - Status should change to "In Progress" (spinning icon)
   - Wait for completion (may take a few minutes depending on PDF size)
   - Status should change to "Completed" (green checkmark)

3. **Test Flashcard Generation:**
   - After Analysis is completed, the **"Run"** button for Flashcards should be enabled
   - Click it to generate flashcards
   - Wait for completion

4. **Test Quiz Generation:**
   - After Flashcards are completed, click **"Run"** for Quiz
   - Wait for completion

5. **Test Indexing:**
   - After Quiz is completed, click **"Run"** for Indexing
   - Wait for completion

### Step 4: Test Error Handling

1. **Test with invalid data:**
   - Try uploading without course code → Should show error
   - Try uploading without PDFs → Should show error

2. **Test failed pipeline stages:**
   - If a stage fails (e.g., API key issue), check the error log
   - Expand the lecture card to see the error message
   - Status should show "Failed" (red X icon)

### Step 5: Test Filtering and Refresh

1. **Filter by Course:**
   - Use the dropdown at the top to filter lectures by course
   - Select "All Courses" to see all lectures

2. **Manual Refresh:**
   - Click the "Refresh" button to manually update the lecture list
   - Useful when checking status of long-running operations

---

## Part 4: Troubleshooting

### Backend Issues

**Problem: PostgreSQL connection failed**
```
Solution:
1. Check if PostgreSQL is running:
   - macOS: brew services list | grep postgresql
   - Linux: sudo systemctl status postgresql
2. Verify POSTGRES_URL in .env file
3. Test connection: psql -U postgres -d self_learning_ai
```

**Problem: Tables not created**
```
Solution:
1. Check backend logs for errors
2. Verify database exists: psql -U postgres -l
3. Check POSTGRES_URL format in .env
```

**Problem: API keys not working**
```
Solution:
1. Verify API keys in .env are correct
2. Check API key quotas/limits
3. Test keys directly with curl or Postman
```

**Problem: R2 upload failed**
```
Solution:
1. Verify CLOUDFLARE_R2_* variables in .env
2. Check R2 bucket exists and is accessible
3. Verify R2 credentials have write permissions
```

### Frontend Issues

**Problem: Cannot access /admin/upload**
```
Solution:
1. Make sure you're logged in (check browser console)
2. Verify route is registered in App.jsx
3. Check for authentication errors in console
```

**Problem: API calls failing**
```
Solution:
1. Check VITE_API_URL in frontend/.env
2. Verify backend is running on port 8000
3. Check browser console for CORS errors
4. Verify ALLOWED_ORIGINS in backend/.env includes http://localhost:5173
```

**Problem: Components not rendering**
```
Solution:
1. Check browser console for errors
2. Verify all dependencies installed: npm install
3. Check for missing imports
```

### Common Errors

**Error: "User not authenticated"**
- Make sure you're logged in via Firebase Auth
- Check Firebase configuration in frontend

**Error: "Failed to fetch"**
- Backend might not be running
- Check CORS configuration
- Verify API URL is correct

**Error: "Database connection failed"**
- PostgreSQL might not be running
- Check POSTGRES_URL format
- Verify database exists

---

## Part 5: Quick Test Checklist

- [ ] PostgreSQL is running
- [ ] Database `self_learning_ai` exists
- [ ] Backend `.env` file configured with all required variables
- [ ] Backend server running on http://localhost:8000
- [ ] Backend health check passes: http://localhost:8000/health
- [ ] Frontend `.env` file configured
- [ ] Frontend server running on http://localhost:5173
- [ ] Can access http://localhost:5173/admin/upload
- [ ] Can upload a PDF successfully
- [ ] Lecture appears in the pipeline list
- [ ] Can trigger Analysis stage
- [ ] Can trigger subsequent stages after prerequisites complete
- [ ] Status updates correctly
- [ ] Error handling works (try invalid input)

---

## Part 6: API Endpoints to Test

You can also test the API directly using the Swagger UI:

1. **Open Swagger UI:** http://localhost:8000/docs

2. **Test Endpoints:**
   - `POST /api/v1/content/ingest` - Upload course content
   - `GET /api/v1/content/courses` - List all courses
   - `GET /api/v1/content/lectures` - List all lectures
   - `POST /api/v1/content/analyze/{lecture_id}` - Trigger analysis
   - `POST /api/v1/content/flashcards/{lecture_id}` - Trigger flashcard generation
   - `POST /api/v1/content/quiz/{lecture_id}` - Trigger quiz generation
   - `POST /api/v1/content/index/{lecture_id}` - Trigger indexing

---

## Part 7: Monitoring

### Backend Logs

Watch backend terminal for:
- Database connection messages
- API request logs
- Pipeline processing logs
- Error messages

### Frontend Console

Open browser DevTools (F12) and check:
- Console for errors
- Network tab for API calls
- Application tab for localStorage/sessionStorage

### Database Verification

Check PostgreSQL to verify data:

```bash
psql -U postgres -d self_learning_ai

# List tables
\dt

# Check courses
SELECT * FROM courses;

# Check lectures
SELECT id, lecture_title, course_code, analysis_status, flashcard_status, quiz_status, qdrant_status FROM lectures;

# Exit
\q
```

---

## Success Indicators

✅ **Backend is working if:**
- Health endpoint returns `{"status": "healthy"}`
- Swagger UI loads at `/docs`
- No errors in terminal

✅ **Frontend is working if:**
- Page loads without errors
- Can see the upload form
- Can see the pipeline list (even if empty)

✅ **Full pipeline is working if:**
- Can upload PDFs successfully
- Lectures appear in the list
- Can trigger pipeline stages
- Status updates correctly
- Data appears in PostgreSQL

---

## Next Steps

After successful testing:

1. **Upload real course content**
2. **Monitor pipeline processing**
3. **Check generated flashcards and quizzes**
4. **Verify data in database**
5. **Test error scenarios**

---

## Support

If you encounter issues:

1. Check backend terminal logs
2. Check browser console
3. Verify all environment variables
4. Test database connection
5. Review error messages carefully

Good luck testing! 🚀

