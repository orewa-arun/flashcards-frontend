#!/bin/bash

# Script to process DAA lectures 5, 6, and 7
# This script runs two commands sequentially for each lecture:
# 1. Flashcard generation
# 2. Copy flashcards to frontend/public and backend/courses (QDRAWN update)

# Script configuration
COURSE_ID="MS5031"
LECTURES=(5 6 7)
BASE_DIR="/Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai"

# Change to project directory
cd "$BASE_DIR"

echo "=========================================="
echo "Processing DAA Lectures 5, 6, and 7"
echo "=========================================="
echo ""

for LECTURE_NUM in "${LECTURES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing DAA Lecture $LECTURE_NUM"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Step 1: Generate flashcards
    echo "🎴 Step 1: Generating flashcards for Lecture $LECTURE_NUM..."
    python -m cognitive_flashcard_generator.learning_materials_cli generate-flashcards \
        --course "$COURSE_ID" \
        --lecture "$LECTURE_NUM" \
        --min-cards 12 || {
        echo "❌ Flashcard generation failed for Lecture $LECTURE_NUM"
        echo "   Continuing to next lecture..."
        echo ""
        continue
    }
    echo "✅ Flashcard generation completed for Lecture $LECTURE_NUM"
    echo ""
    
    # Step 2: Copy flashcards to frontend/public and backend/courses (QDRAWN update)
    echo "📦 Step 2: Copying flashcards to frontend/public and backend/courses (QDRAWN update)..."
    
    # Determine the lecture prefix (e.g., DAA_lec_5)
    LECTURE_PREFIX="DAA_lec_${LECTURE_NUM}"
    FLASHCARD_FILE="${LECTURE_PREFIX}_cognitive_flashcards_only.json"
    SOURCE_PATH="courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}"
    
    if [ ! -f "$SOURCE_PATH" ]; then
        echo "⚠️  Flashcard file not found: $SOURCE_PATH"
        echo "   Skipping copy step for Lecture $LECTURE_NUM"
        echo ""
        continue
    fi
    
    # Create directories if they don't exist
    mkdir -p "frontend/public/courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}"
    mkdir -p "backend/courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}"
    
    # Copy to frontend/public
    cp "$SOURCE_PATH" "frontend/public/courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}" && \
        echo "   ✓ Copied to frontend/public" || {
        echo "   ❌ Failed to copy to frontend/public"
    }
    
    # Copy to backend/courses
    cp "$SOURCE_PATH" "backend/courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}" && \
        echo "   ✓ Copied to backend/courses" || {
        echo "   ❌ Failed to copy to backend/courses"
    }
    
    echo "✅ QDRAWN update completed for Lecture $LECTURE_NUM"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Lecture $LECTURE_NUM processing complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo ""
done

echo "=========================================="
echo "🎉 All lectures processed successfully!"
echo "=========================================="

