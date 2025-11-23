#!/bin/bash

# Script 1: Generate flashcards_only.json for DAA Lectures 6 and 7
# This script generates flashcards from structured_analysis.json files
# NOTE: This script ONLY generates flashcards (flashcards_only.json), NOT quizzes
# Output: flashcards_only.json files in courses/MS5031/cognitive_flashcards/

# Script configuration
COURSE_ID="MS5031"
LECTURES=(6 7)
BASE_DIR="/Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai"

# Change to project directory
cd "$BASE_DIR"

echo "=========================================="
echo "SCRIPT 1: Generate Flashcards"
echo "DAA Lectures 6 and 7 (MS5031)"
echo "=========================================="
echo ""

# Track success/failure
ALL_SUCCESS=true

for LECTURE_NUM in "${LECTURES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing DAA Lecture $LECTURE_NUM"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Generate flashcards
    echo "🎴 Generating flashcards for Lecture $LECTURE_NUM..."
    python -m cognitive_flashcard_generator.learning_materials_cli generate-flashcards \
        --course "$COURSE_ID" \
        --lecture "$LECTURE_NUM" \
        --min-cards 12 || {
        echo "❌ Flashcard generation failed for Lecture $LECTURE_NUM"
        ALL_SUCCESS=false
        echo ""
        continue
    }
    
    # Verify the output file exists
    LECTURE_PREFIX="DAA_lec_${LECTURE_NUM}"
    FLASHCARD_FILE="${LECTURE_PREFIX}_cognitive_flashcards_only.json"
    FLASHCARD_PATH="courses/${COURSE_ID}/cognitive_flashcards/${LECTURE_PREFIX}/${FLASHCARD_FILE}"
    
    if [ -f "$FLASHCARD_PATH" ]; then
        echo "✅ Flashcard generation completed for Lecture $LECTURE_NUM"
        echo "   📄 Output: $FLASHCARD_PATH"
    else
        echo "❌ Flashcard file not found: $FLASHCARD_PATH"
        ALL_SUCCESS=false
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
done

echo "=========================================="
if [ "$ALL_SUCCESS" = true ]; then
    echo "✅ Script 1 Complete: All flashcards generated successfully!"
    echo "   You can now run Script 2 to upload to Qdrant."
    echo "=========================================="
    exit 0
else
    echo "❌ Script 1 Failed: Some flashcards were not generated."
    echo "   Please fix errors before running Script 2."
    echo "=========================================="
    exit 1
fi

