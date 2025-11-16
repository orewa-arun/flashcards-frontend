# Learning Materials Generation - CLI Commands Reference

This document contains all important CLI commands for generating flashcards and quizzes from course content.

## Prerequisites

```bash
# Activate virtual environment
source .venv/bin/activate
```

---

## 1. PDF Slide Processing (Generate structured_analysis.json)

Process PDF slides to extract structured content for slide-based lectures.

### Process all lectures in a course:
```bash
python -m pdf_slide_processor.main MS5260
```

### Process a specific lecture:
```bash
python -m pdf_slide_processor.main MS5260 MIS_lec_5
```

**Output:** `courses/{COURSE_ID}/slide_analysis/{LECTURE_NAME}_structured_analysis.json`

**Example:**
```bash
# Process all MIS lectures
python -m pdf_slide_processor.main MS5260

# Process only MIS Lecture 5
python -m pdf_slide_processor.main MS5260 MIS_lec_5
```

---

## 2. Content Enrichment (For Textbook-Based Lectures)

Generate enhanced content from topics and reference textbooks for lectures without PDFs.

### Enrich a specific lecture:
```bash
python -m cognitive_flashcard_generator.textbook_enrichment --course MS5031 --lecture 2
```

### Enrich all lectures in a course:
```bash
python -m cognitive_flashcard_generator.textbook_enrichment --course MS5031
```

**Output:** `enriched_content/{COURSE_ID}/{COURSE_ID}_lecture_{LECTURE_NUMBER}_enhanced.txt`

**Example:**
```bash
# Enrich DAA Lecture 2 (textbook-based)
python -m cognitive_flashcard_generator.textbook_enrichment --course MS5031 --lecture 2
```

---

## 3. Flashcard Generation

Generate flashcards from structured analysis or enhanced content.

### Generate flashcards for a lecture:
```bash
python -m cognitive_flashcard_generator.learning_materials_cli generate-flashcards \
  --course MS5260 \
  --lecture 5 \
  --min-cards 12
```

**Options:**
- `--course`: Course ID (e.g., MS5260, MS5031, MS5150)
- `--lecture`: Lecture number (e.g., 5, "6-8", "1-3")
- `--min-cards`: Minimum number of cards expected (default: 5)
- `--courses-json`: Path to courses.json (default: courses_resources/courses.json)
- `--output-dir`: Base output directory (default: courses)

**Output:** `courses/{COURSE_ID}/cognitive_flashcards/{COURSE_CODE}_lec_{LECTURE}/{COURSE_CODE}_lec_{LECTURE}_cognitive_flashcards_only.json`

**Examples:**
```bash
# Generate flashcards for MIS Lecture 5
python -m cognitive_flashcard_generator.learning_materials_cli generate-flashcards \
  --course MS5260 \
  --lecture 5

# Generate flashcards for DAA Lecture 2 (textbook-based)
python -m cognitive_flashcard_generator.learning_materials_cli generate-flashcards \
  --course MS5031 \
  --lecture 2 \
  --min-cards 12
```

---

## 4. Quiz Generation

Generate quizzes (all 4 levels) from flashcards.

### Generate quizzes for a lecture:
```bash
python -m cognitive_flashcard_generator.learning_materials_cli generate-quizzes \
  --course MS5260 \
  --lecture 5
```

**Options:**
- `--course`: Course ID (e.g., MS5260, MS5031, MS5150)
- `--lecture`: Lecture number (e.g., 5, "6-8", "1-3")
- `--courses-json`: Path to courses.json (default: courses_resources/courses.json)
- `--output-dir`: Base output directory (default: courses)

**Output:** `courses/{COURSE_ID}/quiz/{COURSE_CODE}_lec_{LECTURE}_level_{1-4}_quiz.json`

**Example:**
```bash
# Generate quizzes for MIS Lecture 5
python -m cognitive_flashcard_generator.learning_materials_cli generate-quizzes \
  --course MS5260 \
  --lecture 5
```

**Note:** Flashcards must be generated first before generating quizzes.

---

## 5. Generate Both Flashcards and Quizzes

Generate both flashcards and quizzes in one command (recommended).

### Generate all learning materials:
```bash
python -m cognitive_flashcard_generator.learning_materials_cli generate-all \
  --course MS5260 \
  --lecture 5 \
  --min-cards 12
```

**Options:** Same as flashcard generation

**Example:**
```bash
# Generate flashcards and quizzes for MIS Lecture 5
python -m cognitive_flashcard_generator.learning_materials_cli generate-all \
  --course MS5260 \
  --lecture 5
```

---

## 6. Validation

Validate that quiz questions' `source_flashcard_id` values match flashcard IDs.

### Validate quiz consistency:
```bash
python -m cognitive_flashcard_generator.validate_quiz_consistency MS5260 5
```

**Usage:**
```bash
python -m cognitive_flashcard_generator.validate_quiz_consistency <course_id> <lecture_number>
```

**Example:**
```bash
# Validate MIS Lecture 5
python -m cognitive_flashcard_generator.validate_quiz_consistency MS5260 5

# Validate DAA Lecture 2
python -m cognitive_flashcard_generator.validate_quiz_consistency MS5031 2
```

**Note:** This validation runs automatically after quiz generation, but you can run it manually to check existing files.

---

## 7. Cleanup Scripts

### Remove Invalid Quiz Questions

Remove questions with missing `source_flashcard_id` from quiz files.

```bash
python remove_invalid_quiz_questions.py <prefix> [--base-dir <dir>]
```

**Examples:**
```bash
# Remove invalid questions from MIS_lec_6-8 quizzes
python remove_invalid_quiz_questions.py MIS_lec_6-8

# Remove invalid questions from DAA_lec_2 quizzes
python remove_invalid_quiz_questions.py DAA_lec_2

# Specify custom base directory
python remove_invalid_quiz_questions.py MIS_lec_6-8 --base-dir backend/courses
```

**What it does:**
- Finds all quiz files matching the prefix (levels 1-4)
- Removes questions with missing/empty `source_flashcard_id`
- Creates backup files (`.bak`) before modifying
- Provides summary of removed questions

---

## Complete Workflow Examples

### For Slide-Based Lectures (e.g., MIS):

```bash
# Step 1: Process PDF slides
python -m pdf_slide_processor.main MS5260 MIS_lec_5

# Step 2: Generate flashcards and quizzes
python -m cognitive_flashcard_generator.learning_materials_cli generate-all \
  --course MS5260 \
  --lecture 5

# Step 3: (Optional) Validate consistency
python -m cognitive_flashcard_generator.validate_quiz_consistency MS5260 5
```

### For Textbook-Based Lectures (e.g., DAA Lecture 2):

```bash
# Step 1: Enrich content from textbook
python -m cognitive_flashcard_generator.textbook_enrichment --course MS5031 --lecture 2

# Step 2: Generate flashcards and quizzes
python -m cognitive_flashcard_generator.learning_materials_cli generate-all \
  --course MS5031 \
  --lecture 2 \
  --min-cards 12

# Step 3: (Optional) Validate consistency
python -m cognitive_flashcard_generator.validate_quiz_consistency MS5031 2
```

### Batch Processing Multiple Lectures:

```bash
# Process all MIS lectures sequentially
python -m pdf_slide_processor.main MS5260 && \
python -m cognitive_flashcard_generator.learning_materials_cli generate-all --course MS5260 --lecture "1-3" && \
python -m cognitive_flashcard_generator.learning_materials_cli generate-all --course MS5260 --lecture 4 && \
python -m cognitive_flashcard_generator.learning_materials_cli generate-all --course MS5260 --lecture 5 && \
python -m cognitive_flashcard_generator.learning_materials_cli generate-all --course MS5260 --lecture "6-8" && \
python -m cognitive_flashcard_generator.learning_materials_cli generate-all --course MS5260 --lecture 9
```

---

## Course IDs and Codes Reference

| Course ID | Course Code | Course Name |
|-----------|-------------|-------------|
| MS5031 | DAA | Data Analysis Applications |
| MS5150 | SI | Strategies and Innovation |
| MS5260 | MIS | Management Information Systems |

---

## Common Issues and Solutions

### Issue: "Content file not found"
**Solution:** Ensure structured_analysis.json exists for slide-based lectures, or run content enrichment for textbook-based lectures.

### Issue: "Flashcards not found" during quiz generation
**Solution:** Generate flashcards first using `generate-flashcards` or `generate-all`.

### Issue: "Quiz validation failed - source_flashcard_ids don't match"
**Solution:** 
1. Check that flashcards have `flashcard_id` fields
2. Regenerate quizzes to ensure consistency
3. Use `remove_invalid_quiz_questions.py` to clean up invalid questions

### Issue: "Generated 7 cards (max recommended: 6)"
**Solution:** This is a warning, not an error. The system will still work, but consider reducing chunk size if JSON truncation occurs.

---

## File Structure

```
courses/
├── {COURSE_ID}/
│   ├── slide_analysis/          # Generated by PDF processor
│   │   └── {LECTURE}_structured_analysis.json
│   ├── cognitive_flashcards/     # Generated flashcards
│   │   └── {COURSE_CODE}_lec_{LECTURE}/
│   │       └── {COURSE_CODE}_lec_{LECTURE}_cognitive_flashcards_only.json
│   └── quiz/                     # Generated quizzes
│       └── {COURSE_CODE}_lec_{LECTURE}_level_{1-4}_quiz.json

enriched_content/                 # Generated by enrichment (textbook-based)
└── {COURSE_ID}/
    └── {COURSE_ID}_lecture_{LECTURE}_enhanced.txt
```

---

## Tips

1. **Always validate after generation:** Run the validation script to ensure consistency
2. **Check chunk sizes:** Slide-based content uses 10K chunks, textbook-based uses 25K chunks
3. **Monitor card counts:** Aim for 5-6 cards per chunk to avoid JSON truncation
4. **Use backups:** The cleanup script creates backups automatically
5. **Process in order:** PDF processing → Flashcard generation → Quiz generation

---

## Quick Reference Card

```bash
# PDF Processing
python -m pdf_slide_processor.main {COURSE_ID} [LECTURE_NAME]

# Content Enrichment (textbook-based only)
python -m cognitive_flashcard_generator.textbook_enrichment --course {COURSE_ID} --lecture {LECTURE}

# Generate All (recommended)
python -m cognitive_flashcard_generator.learning_materials_cli generate-all \
  --course {COURSE_ID} \
  --lecture {LECTURE}

# Validate
python -m cognitive_flashcard_generator.validate_quiz_consistency {COURSE_ID} {LECTURE}

# Cleanup
python remove_invalid_quiz_questions.py {PREFIX}
```

