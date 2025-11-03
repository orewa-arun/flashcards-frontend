# Flashcard ID Implementation

## Overview

Added persistent, unique `flashcard_id` to every flashcard generated. This ensures reliable linking between quiz questions and their source flashcards across the entire system.

## Changes Made

### 1. Flashcard Generation (`cognitive_flashcard_generator/main.py`)

**Location**: `process_course_flashcards()` function, after aggregating all flashcards

**Change**: Added ID generation logic
```python
# Add unique flashcard_id to each flashcard
print(f"🆔 Adding unique flashcard IDs...")
for idx, card in enumerate(flashcards, 1):
    card['flashcard_id'] = f"{lecture_name}_{idx}"
print(f"   ✅ Added IDs from {lecture_name}_1 to {lecture_name}_{len(flashcards)}")
```

**Result**: Every flashcard in `*_cognitive_flashcards_only.json` now has a `flashcard_id` field.

### 2. Quiz Generation (`cognitive_flashcard_generator/main.py`)

**Location**: `process_course_quizzes()` function, when extracting flashcard content

**Change**: Updated to use persistent `flashcard_id` with backward compatibility
```python
# Use persistent flashcard_id if available, otherwise fallback to generated ID
flashcard_id = card.get('flashcard_id', f"{lecture_name}_{idx + 1}")

simplified_card = {
    "id": flashcard_id,  # Now uses persistent ID
    "question": card.get('question', ''),
    ...
}
```

**Result**: Quiz questions now reference the correct, persistent flashcard ID.

## ID Format

### Pattern
```
{lecture_name}_{index}
```

### Examples
- `SI_lec_1_1` - First flashcard from SI_lec_1
- `SI_lec_1_2` - Second flashcard from SI_lec_1
- `OR_lec_1_15` - Fifteenth flashcard from OR_lec_1
- `DAA_lec_4_23` - Twenty-third flashcard from DAA_lec_4

### Properties
- **Unique**: Each flashcard has a distinct ID within its lecture
- **Persistent**: ID remains the same across regenerations (as long as the order is preserved)
- **Predictable**: Sequential numbering starting from 1
- **Human-readable**: Easy to understand and reference
- **Sortable**: Natural ordering by lecture and position

## Flashcard JSON Structure (Updated)

### Before (Old)
```json
{
  "metadata": { ... },
  "flashcards": [
    {
      "type": "concept",
      "question": "What is...",
      "answers": { ... },
      ...
    }
  ]
}
```

### After (New)
```json
{
  "metadata": { ... },
  "flashcards": [
    {
      "flashcard_id": "SI_lec_1_1",  ← NEW FIELD
      "type": "concept",
      "question": "What is...",
      "answers": { ... },
      ...
    }
  ]
}
```

## Quiz JSON Structure (Updated)

The `source_flashcard_id` field in quiz questions now references the persistent `flashcard_id`:

```json
{
  "metadata": { ... },
  "questions": [
    {
      "type": "mcq",
      "question_text": "...",
      "options": { ... },
      "correct_answer": "...",
      "explanation": "...",
      "difficulty_level": 1,
      "source_flashcard_id": "SI_lec_1_1",  ← Now matches flashcard_id
      "tags": [ ... ]
    }
  ]
}
```

## Backward Compatibility

### Existing Flashcard Files
The quiz generation code includes a fallback for older flashcard files that don't have `flashcard_id`:

```python
flashcard_id = card.get('flashcard_id', f"{lecture_name}_{idx + 1}")
```

**Result**: 
- ✅ New flashcard files: Uses persistent `flashcard_id`
- ✅ Old flashcard files: Generates ID on-the-fly (same format)
- ✅ No breaking changes

### Migration Strategy

**Option 1: Gradual (Recommended)**
- New flashcards generated from now on will have IDs
- Old flashcards continue to work with fallback logic
- Regenerate old flashcards as needed

**Option 2: Bulk Regeneration**
- Run flashcard generator for all courses/lectures
- All flashcards will have persistent IDs
- Requires time and API credits

## Benefits

### 1. Reliable Question-Flashcard Linking
```
Question ID: q_12345
Source Flashcard: SI_lec_1_3
✓ Can trace back to exact flashcard content
```

### 2. Analytics & Tracking
- Track which flashcards generate difficult questions
- Identify flashcards that need improvement
- Measure question quality per flashcard

### 3. Future Features Enabled
- **Question Regeneration**: Regenerate questions for specific flashcard
- **Flashcard Updates**: Update flashcard and regenerate related questions
- **Performance Analysis**: Link student performance to specific flashcards
- **Content Recommendations**: Suggest flashcards based on weak areas

### 4. Debugging & Maintenance
- Easy to trace questions back to source
- Quick identification of problematic flashcards
- Better error messages and logging

## Usage Examples

### Generating New Flashcards (with IDs)
```bash
# Generate flashcards (IDs added automatically)
python -m cognitive_flashcard_generator.main MS5150 SI_lec_1

# Output will show:
# 🆔 Adding unique flashcard IDs...
#    ✅ Added IDs from SI_lec_1_1 to SI_lec_1_15
```

### Generating Quizzes (using IDs)
```bash
# Generate quizzes (uses flashcard IDs automatically)
python generate_quizzes.py MS5150 SI_lec_1

# Questions will have:
# "source_flashcard_id": "SI_lec_1_3"
```

### Tracing a Question Back
```python
# Load quiz
with open('courses/MS5150/quiz/SI_lec_1_level_1_quiz.json') as f:
    quiz = json.load(f)

# Get source flashcard ID from a question
question = quiz['questions'][5]
source_id = question['source_flashcard_id']  # e.g., "SI_lec_1_3"

# Load flashcard file
with open('courses/MS5150/cognitive_flashcards/SI_lec_1/SI_lec_1_cognitive_flashcards_only.json') as f:
    flashcards = json.load(f)

# Find the source flashcard
source_flashcard = next(
    (card for card in flashcards['flashcards'] if card['flashcard_id'] == source_id),
    None
)

print(f"Question based on: {source_flashcard['question']}")
```

## Testing

### Verify Flashcard Generation
```bash
# Generate new flashcards
python -m cognitive_flashcard_generator.main MS5150 SI_lec_1

# Check the output JSON
cat courses/MS5150/cognitive_flashcards/SI_lec_1/SI_lec_1_cognitive_flashcards_only.json | grep "flashcard_id"

# Expected output:
#   "flashcard_id": "SI_lec_1_1",
#   "flashcard_id": "SI_lec_1_2",
#   ...
```

### Verify Quiz Generation
```bash
# Generate quizzes
python generate_quizzes.py MS5150 SI_lec_1

# Check quiz questions
cat courses/MS5150/quiz/SI_lec_1_level_1_quiz.json | grep "source_flashcard_id"

# Expected output:
#   "source_flashcard_id": "SI_lec_1_1",
#   "source_flashcard_id": "SI_lec_1_1",
#   "source_flashcard_id": "SI_lec_1_2",
#   ...
```

### Verify Backward Compatibility
```bash
# Quiz generation should still work with old flashcard files
python generate_quizzes.py MS5260 MIS_lec_4

# If flashcard file is old (no flashcard_id), quiz will still generate
# with IDs created on-the-fly
```

## Edge Cases Handled

### 1. Empty Flashcard List
- No IDs generated (no flashcards to ID)
- Process continues normally

### 2. Single Flashcard
- ID: `{lecture_name}_1`
- Works correctly

### 3. Large Number of Flashcards
- IDs scale: `_1`, `_2`, ..., `_99`, `_100`, etc.
- No padding, natural sorting

### 4. Regeneration
- If flashcards are regenerated, IDs will be the same **IF**:
  - Same source content
  - Same order
  - Same total count
- Otherwise, IDs may shift (this is expected behavior)

### 5. Missing flashcard_id Field (Old Files)
- Fallback generates ID on-the-fly
- Uses same format for consistency
- No errors or warnings

## Future Enhancements

### 1. Stable ID Generation
Instead of sequential numbering, use content hashing:
```python
import hashlib
content_hash = hashlib.md5(card['question'].encode()).hexdigest()[:8]
card['flashcard_id'] = f"{lecture_name}_{content_hash}"
```
**Benefit**: IDs remain stable even if flashcard order changes

### 2. Version Tracking
```python
card['flashcard_id'] = f"{lecture_name}_{idx}"
card['flashcard_version'] = 1  # Increment on regeneration
```
**Benefit**: Track flashcard updates over time

### 3. UUID Support
```python
import uuid
card['flashcard_id'] = str(uuid.uuid4())
```
**Benefit**: Globally unique, no collisions

### 4. Hierarchical IDs
```python
card['flashcard_id'] = f"{course_id}.{lecture_name}.{idx}"
# e.g., "MS5150.SI_lec_1.3"
```
**Benefit**: Better organization and scoping

## Impact Summary

### Files Modified
- ✅ `cognitive_flashcard_generator/main.py` (2 changes)

### Lines Added
- 5 lines for flashcard ID generation
- 3 lines for quiz ID consumption
- **Total**: 8 lines

### Breaking Changes
- ❌ None

### Backward Compatibility
- ✅ Full backward compatibility maintained
- ✅ Old flashcard files continue to work
- ✅ Fallback logic for missing IDs

### Testing Required
- ✅ Generate new flashcards
- ✅ Generate quizzes from new flashcards
- ✅ Generate quizzes from old flashcards (backward compat)

## Related Documentation

- `QUIZ_GENERATION_GUIDE.md` - Quiz generation system
- `FLASHCARD_GENERATION_UPDATE.md` - Flashcard generation changes
- `QUIZ_GENERATOR_IMPLEMENTATION_SUMMARY.md` - Quiz generator details

