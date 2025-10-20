# 📊 Analytics System Setup Guide

This guide will help you set up the complete user analytics system that tracks study progress and quiz results using MongoDB Atlas.

## 🎯 What This System Does

- **Anonymous User Tracking**: Generate unique user IDs without collecting personal information
- **Study Progress Analytics**: Track flashcard study progress across different decks
- **Quiz Performance Monitoring**: Record quiz scores, time taken, and detailed question results
- **Privacy Compliance**: GDPR-compliant with cookie consent and opt-out options

## 🚀 Quick Setup (5 minutes)

### Step 1: Set up MongoDB Atlas (Free)

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://cloud.mongodb.com/)
   - Sign up for a free account
   - Create a new cluster (select FREE tier - M0 Sandbox)

2. **Setup Database Access**
   - Go to "Database Access" in the left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `studyapp` (or your choice)
   - Password: Generate a secure password
   - Database User Privileges: "Read and write to any database"
   - Click "Add User"

3. **Setup Network Access**
   - Go to "Network Access" in the left sidebar
   - Click "Add IP Address"
   - Choose "Allow Access from Anywhere" (0.0.0.0/0) for development
   - Click "Confirm"

4. **Get Connection String**
   - Go to "Clusters" and click "Connect" on your cluster
   - Choose "Connect your application"
   - Select "Node.js" and version "4.1 or later"
   - Copy the connection string (looks like: `mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`)
   - Replace `<password>` with your actual password

### Step 2: Configure Backend Environment

1. **Create Environment File**
   ```bash
   cd backend
   cp env.example .env
   ```

2. **Edit `.env` file with your MongoDB details**
   ```env
   # MongoDB Atlas Connection String
   MONGODB_URL=mongodb+srv://studyapp:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority

   # Database Configuration
   DATABASE_NAME=study_analytics

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=True

   # CORS Origins (comma-separated)
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

### Step 3: Install and Run Backend

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run the FastAPI backend
python app/main.py
```

The backend will start at `http://localhost:8000`

### Step 4: Verify Setup

1. **Check Backend Health**
   - Visit: `http://localhost:8000/health`
   - Should show: `{"status": "healthy", "database": "connected"}`

2. **View API Documentation**
   - Visit: `http://localhost:8000/docs`
   - Interactive Swagger UI with all endpoints

3. **Test Frontend**
   - Start your React frontend: `cd frontend && npm run dev`
   - Visit: `http://localhost:5173`
   - You should see the cookie banner on first visit
   - Study some flashcards to test progress tracking
   - Take a quiz to test result tracking

## 📋 Database Collections

The system automatically creates these MongoDB collections:

### `users`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T10:30:00Z",
  "last_active": "2024-01-15T12:45:00Z", 
  "total_decks_studied": 3,
  "total_quiz_attempts": 5
}
```

### `deck_progress`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "MIS_lec_1-3",
  "course_id": "MS5260",
  "progress": 0.75,
  "cards_studied": 15,
  "total_cards": 20,
  "last_studied": "2024-01-15T12:45:00Z",
  "study_streak": 3
}
```

### `quiz_results`
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "deck_id": "MIS_lec_1-3", 
  "course_id": "MS5260",
  "score": 8,
  "total_questions": 10,
  "percentage": 80.0,
  "time_taken": 120,
  "question_results": [
    {
      "question_number": 1,
      "question_type": "mcq", 
      "user_answer": "B",
      "correct_answer": "B",
      "is_correct": true,
      "time_taken": 15
    }
  ],
  "completed_at": "2024-01-15T12:45:00Z"
}
```

## 🔧 API Endpoints

All endpoints require the `X-User-ID` header (automatically added by frontend).

### Analytics Endpoints

- **POST** `/api/v1/analytics/progress` - Update study progress
- **POST** `/api/v1/analytics/quiz-result` - Submit quiz results
- **GET** `/api/v1/analytics/user/{user_id}` - Get user summary

### Health Check

- **GET** `/health` - Check API and database health

## 🍪 Privacy Features

### Cookie Banner
- Appears on first visit
- Users can accept or decline analytics
- Links to privacy policy

### Privacy Policy Page  
- Available at `/privacy-policy`
- Explains data collection practices
- Provides opt-out mechanism

### User Rights
- **Opt-out**: Users can clear their data anytime
- **Transparency**: Clear explanation of data usage
- **Control**: Users control whether analytics is enabled

## 🛠️ Development Tools

### View Database Data
```bash
# Connect to your cluster via MongoDB Compass
# Use the same connection string from your .env file
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test progress tracking (with user ID header)
curl -X POST http://localhost:8000/api/v1/analytics/progress \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test-user-123" \
  -d '{
    "deck_id": "MIS_lec_1-3",
    "course_id": "MS5260", 
    "progress": 0.5,
    "cards_studied": 10,
    "total_cards": 20
  }'
```

### Frontend Analytics Console
Open browser developer tools and check console for analytics messages:
- `Analytics tracking initialized`
- `Progress tracked: {...}`
- `Quiz result tracked: {...}`

## 🚨 Troubleshooting

### Backend Won't Start
1. **Check Python Dependencies**: `pip install -r requirements.txt`
2. **Verify MongoDB URL**: Ensure connection string is correct in `.env`
3. **Check Network Access**: MongoDB Atlas IP whitelist includes your IP

### Database Connection Issues
1. **Wrong Password**: Double-check password in connection string
2. **Network Access**: Ensure 0.0.0.0/0 is whitelisted in MongoDB Atlas
3. **Connection String**: Verify format matches the example

### Frontend Analytics Not Working
1. **Backend Running**: Ensure backend is running on port 8000
2. **CORS Issues**: Check that `http://localhost:5173` is in ALLOWED_ORIGINS
3. **Cookie Consent**: Ensure cookies are accepted in browser
4. **Console Errors**: Check browser developer tools for errors

### No Data in Database
1. **User Consent**: Ensure cookie banner was accepted
2. **Analytics Enabled**: Check that `isAnalyticsEnabled()` returns true
3. **Network Requests**: Check browser network tab for API calls
4. **Backend Logs**: Check backend console for error messages

## 🎯 Production Deployment

For production deployment:

1. **Update CORS Origins**
   ```env
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Secure MongoDB**
   - Use specific IP addresses instead of 0.0.0.0/0
   - Enable additional security features

3. **Environment Variables**
   - Set `DEBUG=False`
   - Use environment-specific database names

4. **HTTPS**
   - Deploy backend with HTTPS
   - Update frontend API URL to HTTPS

## 📈 Next Steps

Once the system is running:

1. **Monitor Usage**: Check MongoDB Atlas metrics
2. **Analyze Data**: Query collections for insights
3. **Optimize Performance**: Add indexes as needed
4. **Scale Up**: Upgrade MongoDB cluster as usage grows

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set correctly  
3. Test each component individually (backend health, frontend console)
4. Check MongoDB Atlas logs and metrics

Your analytics system is now ready to provide valuable insights into how users study and learn! 🎓✨
