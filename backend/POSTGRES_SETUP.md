# PostgreSQL Database Configuration Guide

## Quick Setup

### 1. Create `.env` file in `backend/` directory

Create or edit `backend/.env` file with your PostgreSQL connection details:

```bash
# PostgreSQL Configuration
POSTGRES_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
```

### 2. Connection String Format

The `POSTGRES_URL` follows this format:

```
postgresql+asyncpg://[username]:[password]@[host]:[port]/[database_name]
```

**Components:**
- `username`: Your PostgreSQL username
- `password`: Your PostgreSQL password
- `host`: Database host (usually `localhost` for local)
- `port`: Database port (usually `5432` for PostgreSQL)
- `database_name`: Name of your database

---

## Common Configuration Examples

### Local PostgreSQL (Default)

```bash
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/self_learning_ai
```

### Local with Custom User

```bash
POSTGRES_URL=postgresql+asyncpg://myuser:mypassword@localhost:5432/self_learning_ai
```

### Local with Different Port

```bash
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/self_learning_ai
```

### Remote PostgreSQL Server

```bash
POSTGRES_URL=postgresql+asyncpg://user:pass@db.example.com:5432/self_learning_ai
```

### PostgreSQL with SSL

```bash
POSTGRES_URL=postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=require
```

### PostgreSQL with Special Characters in Password

If your password contains special characters, URL-encode them:

```bash
# Password: my@pass#word
POSTGRES_URL=postgresql+asyncpg://user:my%40pass%23word@localhost:5432/dbname
```

Common encodings:
- `@` → `%40`
- `#` → `%23`
- `%` → `%25`
- `&` → `%26`
- `=` → `%3D`
- `?` → `%3F`

---

## Step-by-Step Setup

### Step 1: Create Database (if it doesn't exist)

Connect to PostgreSQL and create the database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE self_learning_ai;

# Verify it was created
\l

# Exit
\q
```

Or using command line:

```bash
createdb -U postgres self_learning_ai
```

### Step 2: Create `.env` file

In the `backend/` directory, create `.env` file:

```bash
cd backend
touch .env
```

### Step 3: Add PostgreSQL URL

Edit `.env` and add:

```bash
POSTGRES_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/self_learning_ai
```

Replace:
- `postgres` with your PostgreSQL username
- `your_password` with your PostgreSQL password
- `self_learning_ai` with your desired database name

### Step 4: Verify Configuration

The application will automatically:
1. Read `POSTGRES_URL` from `.env`
2. Create connection pool on startup
3. Create tables automatically (if they don't exist)

---

## Configuration Location

### File: `backend/.env`

This is where you set your database connection. The file is loaded by `backend/app/config.py`:

```python
# In config.py
POSTGRES_URL: str = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/self_learning_ai"
)
```

**Default value** (if `POSTGRES_URL` not set):
- Username: `postgres`
- Password: `postgres`
- Host: `localhost`
- Port: `5432`
- Database: `self_learning_ai`

---

## Testing Your Connection

### Option 1: Start the Backend

The backend will automatically test the connection on startup:

```bash
cd backend
python -m app.main
```

Look for these log messages:
```
PostgreSQL connection pool created successfully
Database tables created/verified successfully
PostgreSQL database initialized successfully
```

### Option 2: Test with psql

```bash
psql -U postgres -d self_learning_ai -h localhost -p 5432
```

If you can connect, your credentials are correct.

---

## Troubleshooting

### Error: "connection refused"

**Problem**: Can't connect to PostgreSQL server

**Solutions**:
1. Check if PostgreSQL is running:
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Start PostgreSQL:
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   ```

### Error: "database does not exist"

**Problem**: Database hasn't been created

**Solution**: Create the database:
```bash
createdb -U postgres self_learning_ai
```

### Error: "password authentication failed"

**Problem**: Wrong username or password

**Solution**: 
1. Verify credentials in `.env`
2. Test with psql:
   ```bash
   psql -U your_username -d self_learning_ai
   ```

### Error: "role does not exist"

**Problem**: PostgreSQL user doesn't exist

**Solution**: Create the user:
```sql
CREATE USER your_username WITH PASSWORD 'your_password';
ALTER USER your_username CREATEDB;
```

### Special Characters in Password

If your password has special characters, URL-encode them in the connection string.

---

## Environment Variable Priority

The application reads configuration in this order:

1. **`.env` file** in `backend/` directory (highest priority)
2. **System environment variables**
3. **Default values** in `config.py` (lowest priority)

So if you set `POSTGRES_URL` in your `.env` file, it will be used.

---

## Complete `.env` Example

Here's a complete `.env` file example with all PostgreSQL-related settings:

```bash
# PostgreSQL Configuration
POSTGRES_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/self_learning_ai

# MongoDB Configuration (existing)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=study_analytics

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# AI API Keys
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key

# AI Models
MODEL_ANALYSIS=gemini-2.0-flash-exp
MODEL_FLASHCARDS=claude-3-haiku-20240307
MODEL_QUIZ=gemini-2.0-flash-exp

# Cloudflare R2 (for PDF storage)
CLOUDFLARE_R2_ACCESS_KEY_ID=your_access_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret_key
CLOUDFLARE_R2_ENDPOINT_URL=https://your_account_id.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=course-content
```

---

## Security Notes

⚠️ **Important**: Never commit your `.env` file to git!

The `.env` file should be in `.gitignore`:

```bash
# backend/.gitignore
.env
*.env
```

Use `env.example` (without sensitive data) for documentation.

---

## Quick Reference

| Setting | Location | Format |
|---------|----------|--------|
| PostgreSQL URL | `backend/.env` | `POSTGRES_URL=postgresql+asyncpg://user:pass@host:port/dbname` |
| Config File | `backend/app/config.py` | Reads from `os.getenv("POSTGRES_URL")` |
| Connection Pool | `backend/app/db/postgres.py` | Automatically created on startup |

---

## Next Steps

After configuring PostgreSQL:

1. ✅ Create `.env` file with `POSTGRES_URL`
2. ✅ Start PostgreSQL server
3. ✅ Create database (if needed)
4. ✅ Start backend: `python -m app.main`
5. ✅ Check logs for successful connection
6. ✅ Test API endpoints

The tables will be created automatically on first startup!

