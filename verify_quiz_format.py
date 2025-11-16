#!/usr/bin/env python3
"""
Verify correct_answer format in all quiz files.
Check if MCA questions have arrays vs comma-separated strings.
"""

import json
from pathlib import Path
from collections import defaultdict

def check_quiz_file(quiz_path: Path):
    """Check correct_answer format in a quiz file."""
    try:
        with open(quiz_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {'error': str(e), 'path': str(quiz_path)}
    
    questions = data.get('questions', [])
    issues = []
    stats = {
        'total': len(questions),
        'mcq': 0,
        'mca': 0,
        'mcq_correct': 0,
        'mca_correct': 0,
        'mcq_wrong': 0,
        'mca_wrong': 0,
    }
    
    for idx, question in enumerate(questions, 1):
        question_type = question.get('type', 'mcq')
        correct_answer = question.get('correct_answer')
        
        if question_type == 'mcq':
            stats['mcq'] += 1
            # MCQ should have string
            if isinstance(correct_answer, str):
                stats['mcq_correct'] += 1
            elif isinstance(correct_answer, list):
                if len(correct_answer) == 1:
                    issues.append(f"Q{idx}: MCQ has array ['{correct_answer[0]}'] - should be string")
                    stats['mcq_wrong'] += 1
                else:
                    issues.append(f"Q{idx}: MCQ has multiple answers {correct_answer} - should be MCA type")
                    stats['mcq_wrong'] += 1
            else:
                issues.append(f"Q{idx}: MCQ has invalid correct_answer type: {type(correct_answer).__name__}")
                stats['mcq_wrong'] += 1
                
        elif question_type == 'mca':
            stats['mca'] += 1
            # MCA should have array
            if isinstance(correct_answer, list):
                stats['mca_correct'] += 1
            elif isinstance(correct_answer, str):
                if ',' in correct_answer:
                    issues.append(f"Q{idx}: MCA has comma-separated string '{correct_answer}' - should be array")
                    stats['mca_wrong'] += 1
                else:
                    issues.append(f"Q{idx}: MCA has single string '{correct_answer}' - should be array")
                    stats['mca_wrong'] += 1
            else:
                issues.append(f"Q{idx}: MCA has invalid correct_answer type: {type(correct_answer).__name__}")
                stats['mca_wrong'] += 1
    
    return {
        'path': str(quiz_path),
        'stats': stats,
        'issues': issues,
        'has_issues': len(issues) > 0
    }

def main():
    """Check all quiz files."""
    base_dir = Path(__file__).parent / "backend" / "courses"
    
    quiz_files = list(base_dir.glob("**/quiz/*.json"))
    
    print(f"Found {len(quiz_files)} quiz files\n")
    print("=" * 80)
    
    all_issues = []
    summary = defaultdict(lambda: {'total': 0, 'with_issues': 0, 'fixed_needed': 0})
    
    for quiz_file in sorted(quiz_files):
        result = check_quiz_file(quiz_file)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['path']}")
            print(f"   {result['error']}\n")
            continue
        
        stats = result['stats']
        course_lecture = quiz_file.parent.parent.name + "/" + quiz_file.stem
        
        summary[course_lecture]['total'] += stats['total']
        
        if result['has_issues']:
            summary[course_lecture]['with_issues'] += 1
            summary[course_lecture]['fixed_needed'] += stats['mca_wrong'] + stats['mcq_wrong']
            
            print(f"⚠️  {quiz_file.name}")
            print(f"   MCQ: {stats['mcq']} total, {stats['mcq_correct']} correct, {stats['mcq_wrong']} wrong")
            print(f"   MCA: {stats['mca']} total, {stats['mca_correct']} correct, {stats['mca_wrong']} wrong")
            if result['issues']:
                print(f"   Issues:")
                for issue in result['issues'][:5]:  # Show first 5 issues
                    print(f"     - {issue}")
                if len(result['issues']) > 5:
                    print(f"     ... and {len(result['issues']) - 5} more")
            print()
            all_issues.append(result)
        else:
            print(f"✅ {quiz_file.name} - All correct ({stats['total']} questions)")
    
    print("=" * 80)
    print("\nSUMMARY:")
    print(f"Total quiz files: {len(quiz_files)}")
    print(f"Files with issues: {len(all_issues)}")
    
    if all_issues:
        print(f"\nFiles needing fixes:")
        total_fixes_needed = 0
        for result in all_issues:
            fixes = result['stats']['mca_wrong'] + result['stats']['mcq_wrong']
            total_fixes_needed += fixes
            print(f"  - {Path(result['path']).name}: {fixes} questions need fixing")
        
        print(f"\nTotal questions needing fixes: {total_fixes_needed}")
        print(f"\n💡 Run fix_correct_answer_format.py to fix all issues automatically")

if __name__ == "__main__":
    main()

