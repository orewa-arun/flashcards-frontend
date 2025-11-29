#!/bin/bash
# Export local PostgreSQL database and import to Railway
# 
# Usage:
#   1. Make sure backend/.env has POSTGRES_URL (local) and RAILWAY_PG_URL (Railway)
#   2. Run: ./export_to_railway.sh

# Load environment variables from backend/.env
cd "$(dirname "$0")"
source backend/.env 2>/dev/null || {
  echo "❌ Error: Could not load backend/.env"
  exit 1
}

# Parse local PostgreSQL URL (convert postgresql+asyncpg:// to postgresql://)
LOCAL_URL="${POSTGRES_URL}"
if [[ $LOCAL_URL == postgresql+asyncpg://* ]]; then
  # Remove the asyncpg prefix
  LOCAL_URL="${LOCAL_URL#postgresql+asyncpg://}"
  # Add standard postgresql:// prefix
  LOCAL_URL="postgresql://${LOCAL_URL}"
fi

# Parse Railway PostgreSQL URL
RAILWAY_URL="${RAILWAY_PG_URL}"

if [ -z "$LOCAL_URL" ]; then
  echo "❌ Error: POSTGRES_URL not found in backend/.env"
  exit 1
fi

if [ -z "$RAILWAY_URL" ]; then
  echo "❌ Error: RAILWAY_PG_URL not found in backend/.env"
  exit 1
fi

echo "Local URL: ${LOCAL_URL%%@*}:****@${LOCAL_URL##*@}"
echo "Railway URL: ${RAILWAY_URL%%@*}:****@${RAILWAY_URL##*@}"
echo ""

# Export file
DUMP_FILE="exammate_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "📦 Exporting from local database..."
echo "   Local: $LOCAL_URL"
echo ""

# Export using pg_dump with the connection string
pg_dump "$LOCAL_URL" \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  -f "$DUMP_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Export successful: $DUMP_FILE"
  echo ""
  echo "📤 Importing to Railway..."
  echo "   Railway: ${RAILWAY_URL%%@*}:****@${RAILWAY_URL##*@}"
  echo ""
  
  # Import to Railway
  psql "$RAILWAY_URL" < "$DUMP_FILE"
  
  if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Import successful!"
    echo "🗑️  Cleaning up..."
    rm "$DUMP_FILE"
    echo "✅ Done!"
  else
    echo ""
    echo "❌ Import failed. Dump file kept: $DUMP_FILE"
    echo "   You can manually import with: psql \"\$RAILWAY_PG_URL\" < $DUMP_FILE"
  fi
else
  echo "❌ Export failed"
  exit 1
fi

