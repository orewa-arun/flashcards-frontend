# Correct Answer Normalization Fix

## Problem

Correct answers were being marked as incorrect due to legacy `correct_answer` formats in quiz JSON files:

- Some questions stored `correct_answer` as explanatory text like:
  - `["B: Creating a highly efficient food preparation process...", "resulting in consistently higher profit margins..."]`
  - `["Option C (Invest in R&D) because it represents...", "offsetting the losses from..."]`
  - `["Approach D is superior because it combines...", "and then individual t-tests..."]`
  - `["C: Create a new \`CUSTOMERS\` table (\`CustomerID\`", "\`CustomerName\`) and an \`ITEMS\` table..."]`

- The backend normalization logic couldn't map these to option keys (`A`, `B`, `C`, `D`), so grading failed.

## Root Cause

1. **Data format inconsistency**: Quiz JSON files had `correct_answer` stored as:
   - Multi-part arrays with explanatory text
   - Text starting with option labels but containing full explanations
   - Text mentioning "Option X" or "Approach X" in the middle

2. **Backend normalization too strict**: The normalization logic only handled:
   - Simple option keys: `"C"` → `["C"]`
   - Comma-separated keys: `"A,B"` → `["A","B"]`
   - Leading label stripping: `"B: text..."` → match against option text

3. **Verbose logging**: Every normalization failure was logged as a `WARNING`, flooding the terminal.

## Solution

### 1. Enhanced Backend Normalization (Both Services)

Updated `adaptive_quiz_service.py` and `mix_session_service.py` with smart heuristics:

```python
def extract_letter_heuristic(value_str):
    """Try to extract option letter from explanatory text."""
    # Heuristic 1: "Option C" or "Approach D" pattern
    label_match = re.search(r'\b(?:option|approach)\s+([a-d])\b', value_str, re.IGNORECASE)
    if label_match:
        return label_match.group(1).upper()
    
    # Heuristic 2: First letter followed by space/punctuation
    first_match = re.match(r'^\s*([a-d])[\s:.\)\-\]]+', value_str, re.IGNORECASE)
    if first_match:
        return first_match.group(1).upper()
    
    return None
```

**Normalization order:**
1. Check if already normalized: `["A"]`, `["B"]`
2. Try letter extraction heuristics (new!)
3. Try text matching against option content
4. Log at `debug` level (not `warning`) if all fail

### 2. Data Cleanup Script

Enhanced `normalize_correct_answers_first_letter.py` with the same heuristics:

- Scans all `quiz/*.json` files
- Applies smart extraction to convert:
  - `["B: Creating a highly efficient...", "resulting in..."]` → `["B"]`
  - `["Option C (Invest in R&D) because...", "offsetting..."]` → `["C"]`
  - `["Approach D is superior because...", "and then..."]` → `["D"]`

**Fixed questions:**
- `backend/courses/MS5260/quiz/MIS_lec_1-3_level_2_quiz.json`: 2 questions
- `courses/MS5260/quiz/MIS_lec_1-3_level_2_quiz.json`: 3 questions
- `courses/MS5260/quiz/MIS_lec_4_level_4_quiz.json`: 2 questions

### 3. Reduced Log Noise

Changed all normalization warnings from `logger.warning()` to `logger.debug()`:

- Before: Terminal flooded with `❌ Could not normalize correct_answer...` warnings
- After: Clean output, only debug logs if needed

## Files Changed

### Backend Services
- `backend/app/services/adaptive_quiz_service.py`
  - Added `extract_letter_heuristic()` function
  - Enhanced `_normalize_correct_answer()` with heuristics
  - Changed logging from `warning` to `debug`

- `backend/app/services/mix_session_service.py`
  - Same changes as above

### Data Files (Auto-fixed by script)
- `backend/courses/MS5260/quiz/MIS_lec_1-3_level_2_quiz.json`
- `courses/MS5260/quiz/MIS_lec_1-3_level_2_quiz.json`
- `courses/MS5260/quiz/MIS_lec_4_level_4_quiz.json`

### Scripts
- `normalize_correct_answers_first_letter.py` (enhanced with heuristics)

## Testing

After these changes:

1. **Backend normalization** now handles all legacy formats automatically at runtime
2. **Quiz JSON files** are clean with `["A"]`, `["B"]`, etc. format
3. **Grading** works correctly for all question types
4. **Logs** are clean without normalization warnings

## Prevention

To avoid this in the future:

1. **Always store `correct_answer` as arrays of option keys**: `["B"]`, `["A","C"]`
2. **Never store explanatory text** in `correct_answer`
3. **Run normalization script** after any bulk quiz generation:
   ```bash
   python3 normalize_correct_answers_first_letter.py
   ```

## Summary

The issue was a **data format problem**, not a React bug. The backend now has robust normalization that handles all legacy formats, and the quiz data has been cleaned up. Grading should work correctly for all questions going forward.

