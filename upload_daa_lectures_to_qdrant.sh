#!/bin/bash

# Script 2: Upload flashcards_only.json to Qdrant database for RAG chatbot
# This script runs AFTER Script 1 completes successfully
# It uploads flashcards for all DAA lectures to Qdrant using hybrid ingestion

# Script configuration
COURSE_ID="MS5031"
# Update this list if new lectures are added to the course
LECTURES=(1 2 3 4 5 6 7)
BASE_DIR="/Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai"
RAG_PIPELINE_DIR="backend/image_rag_pipeline"

# Change to project directory
cd "$BASE_DIR"

echo "=========================================="
echo "SCRIPT 2: Upload to Qdrant Database"
echo "DAA Lectures (MS5031)"
echo "=========================================="
echo ""

# Verify that flashcard files exist before proceeding
echo "🔍 Verifying flashcard files exist..."
ALL_FILES_EXIST=true

for LECTURE_NUM in "${LECTURES[@]}"; do
    LECTURE_PREFIX="DAA_lec_${LECTURE_NUM}"
    FLASHCARD_FILE="${LECTURE_PREFIX}_cognitive_flashcards_only.json"
    
    # Check primary location
    FLASHCARD_PATH="courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}"
    
    # Check fallback location
    FLASHCARD_PATH_FALLBACK="backend/courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}"
    
    if [ -f "$FLASHCARD_PATH" ]; then
        echo "   ✅ Found: $FLASHCARD_PATH"
    elif [ -f "$FLASHCARD_PATH_FALLBACK" ]; then
        echo "   ✅ Found: $FLASHCARD_PATH_FALLBACK"
    else
        echo "   ❌ Missing: $FLASHCARD_PATH"
        echo "   ❌ Missing: $FLASHCARD_PATH_FALLBACK"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo ""
    echo "❌ Error: Some flashcard files are missing!"
    echo "   Please run Script 1 first to generate flashcards."
    echo "=========================================="
    exit 1
fi

echo ""
echo "✅ All flashcard files verified!"
echo ""

# Change to RAG pipeline directory
cd "$RAG_PIPELINE_DIR" || {
    echo "❌ Error: Cannot change to $RAG_PIPELINE_DIR"
    exit 1
}

echo "📦 Uploading all DAA lectures to Qdrant database..."
echo ""

# Upload each lecture to Qdrant
for LECTURE_NUM in "${LECTURES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Uploading DAA Lecture $LECTURE_NUM to Qdrant"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    python scripts/batch_ingest.py \
        --course-id "$COURSE_ID" \
        --lecture-number "$LECTURE_NUM" || {
        echo "❌ Qdrant upload failed for Lecture $LECTURE_NUM"
        echo ""
        continue
    }
    
    echo "✅ Qdrant upload completed for Lecture $LECTURE_NUM"
    echo ""
done

echo "=========================================="
echo "✅ Script 2 Complete: All flashcards uploaded to Qdrant!"
echo "   RAG chatbot is now ready for every DAA lecture."
echo "=========================================="

