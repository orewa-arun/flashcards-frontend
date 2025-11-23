#!/bin/bash

# Complete workflow script for DAA Lectures 6 and 7
# Step 1: Generate flashcards for lectures 6 and 7 from structured_analysis.json
# Step 2: Upload ALL lectures (1-7) to Qdrant database for RAG chatbot

# Script configuration
COURSE_ID="MS5031"
LECTURES_TO_GENERATE=(6 7)
BASE_DIR="/Users/arunkumarmurugesan/Documents/entreprenuer-apps/self-learning-ai"
RAG_PIPELINE_DIR="backend/image_rag_pipeline"

# Change to project directory
cd "$BASE_DIR"

echo "=========================================="
echo "DAA Lectures 6 & 7: Complete Workflow"
echo "=========================================="
echo ""

# ============================================================================
# STEP 1: Generate flashcards for lectures 6 and 7
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Generate Flashcards for Lectures 6 & 7"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ALL_SUCCESS=true

for LECTURE_NUM in "${LECTURES_TO_GENERATE[@]}"; do
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
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$ALL_SUCCESS" = false ]; then
    echo "❌ Step 1 Failed: Some flashcards were not generated."
    echo "   Aborting. Please fix errors before proceeding to Step 2."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
else
    echo "✅ Step 1 Complete: All flashcards generated successfully!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo ""

# ============================================================================
# STEP 2: Upload ALL lectures (1-7) to Qdrant database
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Upload ALL Lectures (1-7) to Qdrant Database"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Change to RAG pipeline directory
cd "$RAG_PIPELINE_DIR" || {
    echo "❌ Error: Cannot change to $RAG_PIPELINE_DIR"
    exit 1
}

echo "📦 Uploading ALL DAA lectures (1-7) to Qdrant database..."
echo "   This will process all available flashcard JSON files for MS5031"
echo ""

# Run batch_ingest for the entire course (all lectures 1-7)
python scripts/batch_ingest.py --course-id "$COURSE_ID" || {
    echo ""
    echo "❌ Error: Qdrant upload failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Step 2 Complete: All lectures uploaded to Qdrant!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Return to base directory
cd "$BASE_DIR"

echo "=========================================="
echo "🎉 Complete Workflow Finished!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ Generated flashcards for Lectures 6 & 7"
echo "  ✅ Uploaded ALL lectures (1-7) to Qdrant database"
echo "  ✅ RAG chatbot is now ready for all DAA lectures"
echo "=========================================="

