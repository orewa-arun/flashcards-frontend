# JSON File Mapping Architecture

## Overview

This document explains how the different JSON files in the system are mapped and related to each other, and what keys/identifiers are used to link them.

---

## File Types & Their Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    structured_analysis.json                    │
│  Source: PDF Slide Processing (pdf_slide_processor)           │
│  Location: courses/{course_id}/slide_analysis/                │
│  Format: {lecture_id}_structured_analysis.json                │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             │ Generated from
                             │ (Content Extraction)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              cognitive_flashcards_only.json                    │
│  Source: Flashcard Generator (cognitive_flashcard_generator)   │
│  Location: courses/{course_id}/cognitive_flashcards/          │
│  Format: {lecture_id}_cognitive_flashcards_only.json          │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             │ Generated from
                             │ (Quiz Generator)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Quiz JSON Files (Level 1-4)                 │
│  Source: Quiz Generator (cognitive_flashcard_generator)        │
│  Location: courses/{course_id}/quiz/                           │
│  Format: {lecture_id}_level_{1|2|3|4}_quiz.json               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Identifiers & Mapping

### 1. **Lecture Identifier** (Primary Key)

**Format**: `{course_code}_lec_{lecture_number}`

**Examples**:
- `MIS_lec_1-3` (MS5260, lectures 1-3 combined)
- `DAA_lec_4` (MS5031, lecture 4)
- `SI_lec_1` (MS5150, lecture 1)

**Used in**:
- File naming for all JSON files
- Directory structure
- Metadata fields

**Mapping**:
```python
# From courses.json
course_id: "MS5260"
course_code: "MIS"  # Extracted from course config
lecture_number: "1-3"

# Combined to form:
lecture_id = f"{course_code}_lec_{lecture_number}"
# Result: "MIS_lec_1-3"
```

---

### 2. **Structured Analysis → Flashcards**

#### Mapping Key: `source_chunk`

**In structured_analysis.json**:
```json
{
  "total_slides": 40,
  "slides": [
    {
      "page_number": 1,
      "analysis": {
        "title": "ER Diagram and Database",
        "main_text": "...",
        "key_concepts": [...]
      }
    }
  ]
}
```

**Content Extraction Process**:
1. All slides are extracted and formatted into text chunks
2. Content is chunked (max 6000 chars, with overlap)
3. Each chunk is assigned: `source_chunk = "{lecture_id}_{chunk_index}"`

**In flashcards_only.json**:
```json
{
  "metadata": {
    "source": "DAA_lec_4",  ← Lecture identifier
    "chunks_processed": 6
  },
  "flashcards": [
    {
      "flashcard_id": "DAA_lec_4_1",  ← Unique flashcard ID
      "source_chunk": "DAA_lec_4_1",  ← Links to chunk from structured analysis
      "question": "What is Multiple Linear Regression?",
      "answers": { ... }
    }
  ]
}
```

**Key Fields**:
- `source_chunk`: `"{lecture_id}_{chunk_index}"` (e.g., `"DAA_lec_4_1"`)
- `flashcard_id`: `"{lecture_id}_{flashcard_index}"` (e.g., `"DAA_lec_4_1"`)
- **Note**: `source_chunk` and `flashcard_id` often match, but `flashcard_id` is the primary identifier

---

### 3. **Flashcards → Quiz Questions**

#### Mapping Key: `source_flashcard_id`

**In flashcards_only.json**:
```json
{
  "flashcards": [
    {
      "flashcard_id": "MIS_lec_1-3_1",  ← Primary identifier
      "question": "What is MIS?",
      "answers": { ... },
      "relevance_score": { "score": 10 },
      "tags": ["MIS", "Information Systems"]
    }
  ]
}
```

**In quiz JSON files**:
```json
{
  "metadata": {
    "lecture": "MIS_lec_1-3",  ← Lecture identifier
    "difficulty_level": 1,
    "source_flashcards": 20
  },
  "questions": [
    {
      "type": "mcq",
      "question_text": "Which of the following BEST describes MIS?",
      "correct_answer": ["B"],
      "explanation": "...",
      "difficulty_level": 1,
      "source_flashcard_id": "MIS_lec_1-3_1",  ← Links back to flashcard
      "tags": ["MIS", "Information Systems"]
    }
  ]
}
```

**Key Fields**:
- `source_flashcard_id`: Must match `flashcard_id` from flashcards JSON
- `lecture`: Lecture identifier (same format as in flashcards)

---

## Complete Mapping Flow

### Step 1: PDF → Structured Analysis

**Input**: PDF file (`MIS_lec_4.pdf`)
**Output**: `MIS_lec_4_structured_analysis.json`

**Key Identifiers**:
- File name derived from PDF stem: `Path(pdf_path).stem`
- Each slide has `page_number`

**Code Location**: `pdf_slide_processor/main.py`

---

### Step 2: Structured Analysis → Flashcards

**Input**: `MIS_lec_4_structured_analysis.json`
**Output**: `MIS_lec_4_cognitive_flashcards_only.json`

**Process**:
1. Extract all slide content
2. Chunk content (max 6000 chars per chunk)
3. Generate flashcards from each chunk
4. Assign `source_chunk` and `flashcard_id`

**Mapping**:
```python
# In cognitive_flashcard_generator/main.py
for i, chunk in enumerate(content_chunks, 1):
    chunk_flashcards = generator.generate_flashcards(chunk, lecture_name)
    for card in chunk_flashcards:
        card['source_chunk'] = f"{lecture_name}_{i}"  # e.g., "MIS_lec_4_1"

# After all flashcards generated
for idx, card in enumerate(flashcards, 1):
    card['flashcard_id'] = f"{lecture_name}_{idx}"  # e.g., "MIS_lec_4_1"
```

**Key Identifiers**:
- `source_chunk`: `"{lecture_id}_{chunk_index}"`
- `flashcard_id`: `"{lecture_id}_{flashcard_index}"`

**Code Location**: `cognitive_flashcard_generator/main.py` (lines 413, 431)

---

### Step 3: Flashcards → Quiz Questions

**Input**: `MIS_lec_4_cognitive_flashcards_only.json`
**Output**: `MIS_lec_4_level_{1|2|3|4}_quiz.json`

**Process**:
1. Load flashcards for lecture
2. Generate questions at different difficulty levels
3. Link each question to source flashcard

**Mapping**:
```python
# In cognitive_flashcard_generator/main.py (quiz generation)
flashcard_id = card.get('flashcard_id', f"{lecture_name}_{idx + 1}")

simplified_card = {
    "id": flashcard_id,  # Used as source_flashcard_id
    "question": card.get('question', ''),
    ...
}

# When generating quiz questions
question = {
    "question_text": "...",
    "source_flashcard_id": flashcard_id,  # Links back to flashcard
    ...
}
```

**Key Identifiers**:
- `source_flashcard_id`: Must match `flashcard_id` from flashcards

**Code Location**: `cognitive_flashcard_generator/quiz_generator.py`

---

## Identifier Summary Table

| File Type | Primary Key | Secondary Keys | Links To |
|-----------|------------|----------------|----------|
| **structured_analysis.json** | `lecture_id` (from filename) | `page_number` (per slide) | → Flashcards (via content extraction) |
| **flashcards_only.json** | `flashcard_id` | `source_chunk`, `lecture_id` (metadata) | → Quiz questions (via `source_flashcard_id`) |
| **quiz JSON** | `source_flashcard_id` | `lecture` (metadata), `difficulty_level` | ← Flashcards (via `flashcard_id`) |

---

## Example: Complete Trace

### Starting Point: PDF File
```
File: MIS_lec_4.pdf
Location: courses_resources/MS5260/lecture_slides/
```

### Step 1: Structured Analysis
```
File: MIS_lec_4_structured_analysis.json
Location: courses/MS5260/slide_analysis/
Content: 40 slides with page_number, analysis, etc.
```

### Step 2: Flashcards
```
File: MIS_lec_4_cognitive_flashcards_only.json
Location: courses/MS5260/cognitive_flashcards/MIS_lec_4/
Content:
  - metadata.source: "MIS_lec_4"
  - flashcards[0].flashcard_id: "MIS_lec_4_1"
  - flashcards[0].source_chunk: "MIS_lec_4_1"
```

### Step 3: Quiz Questions
```
Files: 
  - MIS_lec_4_level_1_quiz.json
  - MIS_lec_4_level_2_quiz.json
  - MIS_lec_4_level_3_quiz.json
  - MIS_lec_4_level_4_quiz.json
Location: courses/MS5260/quiz/
Content:
  - metadata.lecture: "MIS_lec_4"
  - questions[0].source_flashcard_id: "MIS_lec_4_1"  ← Links to flashcard
```

---

## Validation & Consistency

### Flashcard-Quiz Consistency Check

The system includes validation to ensure quiz questions reference valid flashcards:

**Code**: `cognitive_flashcard_generator/validate_quiz_consistency.py`

**Checks**:
1. All `source_flashcard_id` values in quiz files exist in flashcards
2. All flashcards have corresponding quiz questions (optional)

**Example**:
```python
# Valid
flashcard_id: "MIS_lec_4_1"
source_flashcard_id: "MIS_lec_4_1"  ✅ Match

# Invalid
flashcard_id: "MIS_lec_4_1"
source_flashcard_id: "MIS_lec_4_99"  ❌ Not found
```

---

## Backend Usage

### Adaptive Quiz Service

**Code**: `backend/app/services/adaptive_quiz_service.py`

**Process**:
1. Load flashcards: Creates mapping `flashcard_id → metadata`
2. Load quiz questions: Filters by `source_flashcard_id`
3. Matches questions to flashcards for performance tracking

```python
# Load flashcards
flashcard_map = {}
for card in flashcards:
    flashcard_id = card.get('flashcard_id')
    flashcard_map[flashcard_id] = {
        'relevance_score': card.get('relevance_score', {}).get('score', 0),
        'question': card.get('question', ''),
        'tags': card.get('tags', [])
    }

# Load quiz questions
for question in quiz_questions:
    source_id = question.get('source_flashcard_id')
    flashcard_meta = flashcard_map.get(source_id)  # Lookup
    # Use metadata for adaptive selection
```

---

## Key Takeaways

1. **Primary Linking Key**: `lecture_id` (format: `{course_code}_lec_{number}`)
   - Used in file naming
   - Used in metadata
   - Links all related files

2. **Flashcard → Quiz Linking**: `flashcard_id` ↔ `source_flashcard_id`
   - Must match exactly
   - Enables traceability
   - Used for performance tracking

3. **Content Flow**:
   ```
   PDF → structured_analysis.json → flashcards_only.json → quiz JSON files
   ```

4. **Identifier Format**:
   - `flashcard_id`: `"{lecture_id}_{index}"` (e.g., `"MIS_lec_4_1"`)
   - `source_chunk`: `"{lecture_id}_{chunk_index}"` (often same as flashcard_id)
   - `source_flashcard_id`: Must match `flashcard_id`

5. **Validation**: System validates flashcard-quiz consistency to prevent broken links

---

## File Location Patterns

```
courses/
└── {course_id}/
    ├── slide_analysis/
    │   └── {lecture_id}_structured_analysis.json
    ├── cognitive_flashcards/
    │   └── {lecture_id}/
    │       └── {lecture_id}_cognitive_flashcards_only.json
    └── quiz/
        ├── {lecture_id}_level_1_quiz.json
        ├── {lecture_id}_level_2_quiz.json
        ├── {lecture_id}_level_3_quiz.json
        └── {lecture_id}_level_4_quiz.json
```

**Example**:
```
courses/
└── MS5260/
    ├── slide_analysis/
    │   └── MIS_lec_4_structured_analysis.json
    ├── cognitive_flashcards/
    │   └── MIS_lec_4/
    │       └── MIS_lec_4_cognitive_flashcards_only.json
    └── quiz/
        ├── MIS_lec_4_level_1_quiz.json
        ├── MIS_lec_4_level_2_quiz.json
        ├── MIS_lec_4_level_3_quiz.json
        └── MIS_lec_4_level_4_quiz.json
```

---

## Summary

**The mapping is done through**:

1. **Lecture Identifier** (`lecture_id`): Primary key linking all files
   - Format: `{course_code}_lec_{lecture_number}`
   - Used in: File names, metadata, directory structure

2. **Flashcard ID** (`flashcard_id`): Links flashcards to quiz questions
   - Format: `{lecture_id}_{index}`
   - In flashcards: `flashcard_id` field
   - In quiz: `source_flashcard_id` field (must match)

3. **Source Chunk** (`source_chunk`): Links flashcards to structured analysis chunks
   - Format: `{lecture_id}_{chunk_index}`
   - Tracks which content chunk generated the flashcard

**All files are related by the lecture identifier, with flashcards serving as the bridge between structured analysis and quiz questions.**

