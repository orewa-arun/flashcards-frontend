# Database Migration Scripts for Production

This document contains all SQL migration commands for features shipped recently. Run these in your production database.

**Note:** All commands use `IF NOT EXISTS` and `IF NOT EXISTS` clauses to make them idempotent - safe to run multiple times.

---

## Complete Migration Script

Run this entire block in your production PostgreSQL database:

```sql
BEGIN;

-- ============================================================================
-- 1. COURSE REPOSITORY + MULTI-ORGANIZATION SUPPORT
-- ============================================================================

-- Add repository link and multi-org columns to courses table
ALTER TABLE courses
  ADD COLUMN IF NOT EXISTS course_repository_link TEXT,
  ADD COLUMN IF NOT EXISTS repository_created_by TEXT,
  ADD COLUMN IF NOT EXISTS college TEXT;

-- Index for college-based filtering
CREATE INDEX IF NOT EXISTS idx_courses_college
  ON courses(college);

-- Ensure course_code index exists (safe to run even if already exists)
CREATE INDEX IF NOT EXISTS idx_courses_course_code
  ON courses(course_code);

-- ============================================================================
-- 2. MULTI-REGION / MULTI-ORGANIZATION USER SUPPORT
-- ============================================================================

-- Add college, country, and timezone columns to users table
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS college TEXT,
  ADD COLUMN IF NOT EXISTS country TEXT,
  ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'Asia/Kolkata';

-- Index for college-based filtering
CREATE INDEX IF NOT EXISTS idx_users_college
  ON users(college);

-- Ensure user indexes exist (safe to run even if already exists)
CREATE INDEX IF NOT EXISTS idx_users_firebase_uid
  ON users(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_users_email
  ON users(email);

-- ============================================================================
-- 3. COURSE REPOSITORY HISTORY (AUDIT TRAIL)
-- ============================================================================

-- Create course_repository_history table for tracking repository link changes
CREATE TABLE IF NOT EXISTS course_repository_history (
  id SERIAL PRIMARY KEY,
  course_code VARCHAR(255) NOT NULL REFERENCES courses(course_code) ON DELETE CASCADE,
  repository_link TEXT NOT NULL,
  updated_by_name TEXT,
  updated_by_uid VARCHAR(255),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for repository history
CREATE INDEX IF NOT EXISTS idx_repo_history_course_code
  ON course_repository_history(course_code);

CREATE INDEX IF NOT EXISTS idx_repo_history_updated_at
  ON course_repository_history(course_code, updated_at DESC);

-- ============================================================================
-- 4. EXAM READINESS FEATURE
-- ============================================================================

-- Create user_exam_readiness table for storing exam readiness scores
CREATE TABLE IF NOT EXISTS user_exam_readiness (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  exam_id VARCHAR(255) NOT NULL,
  course_id VARCHAR(255) NOT NULL,
  overall_readiness_score FLOAT NOT NULL DEFAULT 0.0,
  coverage_factor FLOAT NOT NULL DEFAULT 0.0,
  accuracy_factor FLOAT NOT NULL DEFAULT 0.0,
  momentum_factor FLOAT NOT NULL DEFAULT 0.0,
  raw_scores JSONB DEFAULT '{}'::jsonb,
  max_possible_scores JSONB DEFAULT '{}'::jsonb,
  weak_flashcards JSONB DEFAULT '[]'::jsonb,
  total_flashcards_in_exam INTEGER NOT NULL DEFAULT 0,
  flashcards_attempted INTEGER NOT NULL DEFAULT 0,
  last_calculated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, exam_id)
);

-- Indexes for exam readiness
CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_user
  ON user_exam_readiness(user_id);
CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_user_exam
  ON user_exam_readiness(user_id, exam_id);
CREATE INDEX IF NOT EXISTS idx_user_exam_readiness_course
  ON user_exam_readiness(user_id, course_id);

-- ============================================================================
-- 5. EXAM TIMETABLE FEATURE
-- ============================================================================

-- Create course_timetables table for storing exam schedules
CREATE TABLE IF NOT EXISTS course_timetables (
  id SERIAL PRIMARY KEY,
  course_id VARCHAR(255) UNIQUE NOT NULL,
  exams JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for course timetables
CREATE INDEX IF NOT EXISTS idx_course_timetables_course
  ON course_timetables(course_id);

-- ============================================================================
-- 6. FLASHCARD CHAT FEATURE (Separate from AI Tutor)
-- ============================================================================

-- Create flashcard_chats table for flashcard-specific chat sessions
CREATE TABLE IF NOT EXISTS flashcard_chats (
  id SERIAL PRIMARY KEY,
  chat_id UUID UNIQUE NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  course_id VARCHAR(255) NOT NULL,
  lecture_id VARCHAR(255) NOT NULL,
  flashcard_id VARCHAR(255) NOT NULL,
  flashcard_context JSONB NOT NULL,
  message_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, flashcard_id)
);

-- Indexes for flashcard chats
CREATE INDEX IF NOT EXISTS idx_flashcard_chats_chat_id
  ON flashcard_chats(chat_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_chats_user
  ON flashcard_chats(user_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_chats_user_flashcard
  ON flashcard_chats(user_id, flashcard_id);

-- Create flashcard_chat_messages table for storing chat messages
CREATE TABLE IF NOT EXISTS flashcard_chat_messages (
  id SERIAL PRIMARY KEY,
  chat_id UUID NOT NULL REFERENCES flashcard_chats(chat_id) ON DELETE CASCADE,
  role VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for flashcard chat messages
CREATE INDEX IF NOT EXISTS idx_flashcard_chat_messages_chat
  ON flashcard_chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_flashcard_chat_messages_timestamp
  ON flashcard_chat_messages(chat_id, timestamp);

COMMIT;
```

---

## Feature Summary

### 1. Course Repository Link
- Added `course_repository_link` and `repository_created_by` columns to `courses` table
- Created `course_repository_history` table for audit trail

### 2. Multi-Organization Support
- Added `college`, `country`, and `timezone` columns to `users` table
- Added `college` column to `courses` table for filtering
- Created indexes for efficient college-based queries

### 3. Exam Readiness Score
- Created `user_exam_readiness` table for storing per-exam readiness scores
- Calculates readiness based on flashcard performance from `user_flashcard_performance` table

### 4. Exam Timetable
- Created `course_timetables` table for storing exam schedules per course
- Supports timezone-aware scheduling

### 5. Flashcard Chat
- Created `flashcard_chats` table for flashcard-specific chat sessions
- Created `flashcard_chat_messages` table for storing chat messages
- Separate from AI Tutor conversations system
- Stores flashcard context (question + answers) on first message

---

## Verification Queries

After running the migration, verify with these queries:

```sql
-- Check courses table has new columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'courses' 
  AND column_name IN ('course_repository_link', 'repository_created_by', 'college');

-- Check users table has new columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('college', 'country', 'timezone');

-- Check all new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'course_repository_history',
    'user_exam_readiness',
    'course_timetables',
    'flashcard_chats',
    'flashcard_chat_messages'
  )
ORDER BY table_name;
```

---

## Rollback (if needed)

If you need to rollback, run these in reverse order:

```sql
BEGIN;

-- Drop flashcard chat tables
DROP TABLE IF EXISTS flashcard_chat_messages CASCADE;
DROP TABLE IF EXISTS flashcard_chats CASCADE;

-- Drop timetable table
DROP TABLE IF EXISTS course_timetables CASCADE;

-- Drop exam readiness table
DROP TABLE IF EXISTS user_exam_readiness CASCADE;

-- Drop repository history table
DROP TABLE IF EXISTS course_repository_history CASCADE;

-- Remove columns from users table
ALTER TABLE users
  DROP COLUMN IF EXISTS college,
  DROP COLUMN IF EXISTS country,
  DROP COLUMN IF EXISTS timezone;

-- Remove columns from courses table
ALTER TABLE courses
  DROP COLUMN IF EXISTS course_repository_link,
  DROP COLUMN IF EXISTS repository_created_by,
  DROP COLUMN IF EXISTS college;

COMMIT;
```

---

**Last Updated:** 2025-01-27
**Migration Version:** 1.0

