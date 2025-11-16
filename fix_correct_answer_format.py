#!/usr/bin/env python3
"""
Fix correct_answer format in quiz files.
For MCA questions, convert "A,B,C" to ["A", "B", "C"]
"""

import json
from pathlib import Path

def fix_quiz_file(quiz_path: Path):
    """Fix correct_answer format in a quiz file - convert everything to arrays."""
    print(f"Processing {quiz_path}...")
    
    with open(quiz_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data.get('questions', [])
    modified = False
    fixes_made = []
    
    for idx, question in enumerate(questions, 1):
        correct_answer = question.get('correct_answer')
        question_type = question.get('type', 'mcq')
        
        # Convert everything to arrays for consistency
        if isinstance(correct_answer, str):
            # String format -> convert to array
            if ',' in correct_answer:
                # Comma-separated string -> array
                answer_array = [ans.strip() for ans in correct_answer.split(',')]
                question['correct_answer'] = answer_array
                fixes_made.append(f"Q{idx}: {question_type.upper()} '{correct_answer}' -> {answer_array}")
                modified = True
            else:
                # Single string -> single-element array
                answer_array = [correct_answer.strip()]
                question['correct_answer'] = answer_array
                fixes_made.append(f"Q{idx}: {question_type.upper()} '{correct_answer}' -> {answer_array}")
                modified = True
        elif isinstance(correct_answer, list):
            # Already an array - validate it's correct
            if len(correct_answer) == 0:
                fixes_made.append(f"Q{idx}: Empty array - SKIPPED (needs manual fix)")
                continue
            
            # Check if MCQ has multiple answers (should be MCA)
            if question_type == 'mcq' and len(correct_answer) > 1:
                fixes_made.append(f"Q{idx}: MCQ has {len(correct_answer)} answers {correct_answer} - keeping as array (should be MCA type)")
                # Keep as array but note the issue
                modified = True
            # Array is already correct format, no change needed
        else:
            fixes_made.append(f"Q{idx}: Invalid type {type(correct_answer).__name__} - SKIPPED")
    
    if modified:
        for fix in fixes_made[:5]:  # Show first 5 fixes
            print(f"  - {fix}")
        if len(fixes_made) > 5:
            print(f"  ... and {len(fixes_made) - 5} more fixes")
        with open(quiz_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Fixed {len(fixes_made)} question(s) in {quiz_path.name}")
    else:
        print(f"  - No changes needed")
    
    return modified

def main():
    """Fix all quiz files in the backend/courses directory."""
    base_dir = Path(__file__).parent / "backend" / "courses"
    
    # Fix all quiz files
    quiz_files = list(base_dir.glob("**/quiz/*.json"))
    
    print(f"Found {len(quiz_files)} quiz files\n")
    
    fixed_count = 0
    for quiz_file in quiz_files:
        if fix_quiz_file(quiz_file):
            fixed_count += 1
    
    print(f"\n✓ Fixed {fixed_count} quiz files")

if __name__ == "__main__":
    main()

