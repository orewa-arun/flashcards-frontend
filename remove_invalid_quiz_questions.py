"""
Script to remove questions with missing source_flashcard_id from quiz files.

Usage:
    python remove_invalid_quiz_questions.py MIS_lec_6-8
    python remove_invalid_quiz_questions.py DAA_lec_2 --base-dir courses
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def find_quiz_files(prefix: str, base_dir: Path = Path("courses")) -> List[Path]:
    """
    Find all quiz files matching the prefix across all course directories.
    
    Args:
        prefix: Quiz file prefix (e.g., "MIS_lec_6-8" or "DAA_lec_2")
        base_dir: Base directory containing course directories
        
    Returns:
        List of quiz file paths
    """
    quiz_files = []
    
    # Search in all course directories
    for course_dir in base_dir.iterdir():
        if not course_dir.is_dir():
            continue
        
        quiz_dir = course_dir / "quiz"
        if not quiz_dir.exists():
            continue
        
        # Find all quiz files matching the prefix
        for level in range(1, 5):
            quiz_file = quiz_dir / f"{prefix}_level_{level}_quiz.json"
            if quiz_file.exists():
                quiz_files.append(quiz_file)
    
    return quiz_files


def remove_invalid_questions(quiz_file: Path) -> tuple[int, int]:
    """
    Remove questions with missing source_flashcard_id from a quiz file.
    
    Args:
        quiz_file: Path to quiz JSON file
        
    Returns:
        Tuple of (original_count, new_count, removed_count)
    """
    with open(quiz_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    questions = data.get('questions', [])
    original_count = len(questions)
    
    # Filter out questions with missing source_flashcard_id
    valid_questions = [
        q for q in questions
        if q.get('source_flashcard_id') is not None and q.get('source_flashcard_id') != ''
    ]
    
    removed_count = original_count - len(valid_questions)
    
    if removed_count > 0:
        # Update the data with valid questions only
        data['questions'] = valid_questions
        
        # Create backup
        backup_file = quiz_file.with_suffix('.json.bak')
        quiz_file.rename(backup_file)
        
        # Save cleaned data
        with open(quiz_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Removed {removed_count} invalid question(s) from {quiz_file.name}")
        print(f"    Backup saved to: {backup_file.name}")
    
    return original_count, len(valid_questions), removed_count


def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python remove_invalid_quiz_questions.py <prefix> [--base-dir <dir>]")
        print("Example: python remove_invalid_quiz_questions.py MIS_lec_6-8")
        print("Example: python remove_invalid_quiz_questions.py DAA_lec_2 --base-dir courses")
        sys.exit(1)
    
    prefix = sys.argv[1]
    base_dir = Path("courses")
    
    # Parse optional base-dir argument
    if "--base-dir" in sys.argv:
        idx = sys.argv.index("--base-dir")
        if idx + 1 < len(sys.argv):
            base_dir = Path(sys.argv[idx + 1])
    
    print(f"🔍 Searching for quiz files with prefix: {prefix}")
    print(f"📁 Base directory: {base_dir}\n")
    
    quiz_files = find_quiz_files(prefix, base_dir)
    
    if not quiz_files:
        print(f"❌ No quiz files found matching prefix '{prefix}'")
        print(f"   Searched in: {base_dir}/*/quiz/")
        sys.exit(1)
    
    print(f"📊 Found {len(quiz_files)} quiz file(s):")
    for qf in quiz_files:
        print(f"   - {qf}")
    print()
    
    total_original = 0
    total_valid = 0
    total_removed = 0
    
    for quiz_file in quiz_files:
        original, valid, removed = remove_invalid_questions(quiz_file)
        total_original += original
        total_valid += valid
        total_removed += removed
    
    print(f"\n{'='*70}")
    print(f"✅ CLEANUP COMPLETE")
    print(f"{'='*70}")
    print(f"📊 Summary:")
    print(f"   Files processed: {len(quiz_files)}")
    print(f"   Original questions: {total_original}")
    print(f"   Valid questions: {total_valid}")
    print(f"   Removed questions: {total_removed}")
    print(f"{'='*70}\n")
    
    if total_removed > 0:
        print("💡 Tip: Backup files (.bak) have been created. You can restore them if needed.")
    else:
        print("✨ All questions already have valid source_flashcard_id values!")


if __name__ == "__main__":
    main()

