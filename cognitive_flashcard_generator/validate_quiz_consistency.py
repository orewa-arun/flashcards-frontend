"""
Quiz Consistency Validator - Ensures flashcard IDs match quiz source_flashcard_ids.

This prevents runtime errors where the backend can't match quiz questions to flashcards.
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Tuple


def validate_flashcard_quiz_consistency(
    course_id: str,
    lecture_number: str,
    base_dir: Path = None,
    courses_json_path: str = "courses_resources/courses.json"
) -> Tuple[bool, List[str]]:
    """
    Validate that quiz source_flashcard_ids match flashcard flashcard_ids.
    
    Args:
        course_id: Course ID (e.g., "MS5031")
        lecture_number: Lecture number (e.g., "2")
        base_dir: Base directory for courses (defaults to "courses/")
        courses_json_path: Path to courses.json file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if base_dir is None:
        base_dir = Path("courses")
    
    errors = []
    
    # Load course_code from courses.json dynamically
    course_code = None
    try:
        courses_json = Path(courses_json_path)
        if courses_json.exists():
            with open(courses_json, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
            
            for course in courses_data:
                if course.get('course_id') == course_id:
                    course_code = course.get('course_code')
                    break
    except Exception as e:
        # Fallback to hardcoded map if courses.json can't be loaded
        pass
    
    # Fallback to hardcoded map if course_code not found
    if not course_code:
        course_code_map = {
            "MS5031": "DAA",
            "MS5150": "SI",
            "MS5260": "MIS",
        }
        course_code = course_code_map.get(course_id, course_id)
    
    # Load flashcards
    flashcard_dir = base_dir / course_id / "cognitive_flashcards" / f"{course_code}_lec_{lecture_number}"
    flashcard_file = flashcard_dir / f"{course_code}_lec_{lecture_number}_cognitive_flashcards_only.json"
    
    if not flashcard_file.exists():
        errors.append(f"Flashcard file not found: {flashcard_file}")
        return False, errors
    
    try:
        with open(flashcard_file, 'r', encoding='utf-8') as f:
            flashcard_data = json.load(f)
        
        flashcards = flashcard_data.get('flashcards', [])
        flashcard_ids = {fc.get('flashcard_id') for fc in flashcards if fc.get('flashcard_id')}
        
        if not flashcard_ids:
            errors.append(f"No flashcard_ids found in {flashcard_file}")
            return False, errors
        
        print(f"✓ Found {len(flashcard_ids)} flashcards with IDs")
    
    except Exception as e:
        errors.append(f"Error loading flashcards: {e}")
        return False, errors
    
    # Load and validate all quiz levels
    quiz_dir = base_dir / course_id / "quiz"
    
    if not quiz_dir.exists():
        errors.append(f"Quiz directory not found: {quiz_dir}")
        return False, errors
    
    total_questions = 0
    valid_questions = 0
    
    for level in range(1, 5):
        quiz_file = quiz_dir / f"{course_code}_lec_{lecture_number}_level_{level}_quiz.json"
        
        if not quiz_file.exists():
            errors.append(f"Quiz file not found: {quiz_file}")
            continue
        
        try:
            with open(quiz_file, 'r', encoding='utf-8') as f:
                quiz_data = json.load(f)
            
            questions = quiz_data.get('questions', [])
            
            for idx, q in enumerate(questions, 1):
                total_questions += 1
                source_id = q.get('source_flashcard_id')
                
                if not source_id:
                    errors.append(f"Level {level}, Question {idx}: Missing source_flashcard_id")
                    continue
                
                if source_id not in flashcard_ids:
                    errors.append(
                        f"Level {level}, Question {idx}: Invalid source_flashcard_id '{source_id}' "
                        f"(not in flashcard IDs)"
                    )
                else:
                    valid_questions += 1
        
        except Exception as e:
            errors.append(f"Error loading quiz level {level}: {e}")
    
    # Summary
    if errors:
        print(f"\n❌ Validation FAILED")
        print(f"   Total questions: {total_questions}")
        print(f"   Valid questions: {valid_questions}")
        print(f"   Errors: {len(errors)}")
        return False, errors
    else:
        print(f"\n✅ Validation PASSED")
        print(f"   Total questions: {total_questions}")
        print(f"   All source_flashcard_ids match flashcard_ids")
        return True, []


def validate_flashcards_have_ids(flashcard_file: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all flashcards have flashcard_id field.
    
    Args:
        flashcard_file: Path to flashcard JSON file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not flashcard_file.exists():
        errors.append(f"Flashcard file not found: {flashcard_file}")
        return False, errors
    
    try:
        with open(flashcard_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        flashcards = data.get('flashcards', [])
        
        if not flashcards:
            errors.append("No flashcards found in file")
            return False, errors
        
        missing_ids = []
        for idx, fc in enumerate(flashcards, 1):
            if 'flashcard_id' not in fc or not fc['flashcard_id']:
                missing_ids.append(idx)
        
        if missing_ids:
            errors.append(f"Flashcards missing flashcard_id: {missing_ids}")
            return False, errors
        
        print(f"✅ All {len(flashcards)} flashcards have flashcard_id")
        return True, []
    
    except Exception as e:
        errors.append(f"Error validating flashcards: {e}")
        return False, errors


def main():
    """CLI for validation script."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python validate_quiz_consistency.py <course_id> <lecture_number>")
        print("Example: python validate_quiz_consistency.py MS5031 2")
        sys.exit(1)
    
    course_id = sys.argv[1]
    lecture_number = sys.argv[2]
    
    print(f"Validating quiz consistency for {course_id} Lecture {lecture_number}...")
    print("=" * 70)
    
    is_valid, errors = validate_flashcard_quiz_consistency(course_id, lecture_number)
    
    if not is_valid:
        print("\n⚠️  ERRORS FOUND:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)
    else:
        print("\n🎉 All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

