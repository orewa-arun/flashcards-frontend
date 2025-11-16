"""
Learning Materials CLI

Command-line interface for generating flashcards and quizzes from
both slide-based and textbook-based content.

Usage:
    # Generate flashcards only
    python learning_materials_cli.py generate-flashcards --course MS5031 --lecture 2
    
    # Generate quizzes only
    python learning_materials_cli.py generate-quizzes --course MS5031 --lecture 2
    
    # Generate both (default)
    python learning_materials_cli.py generate-all --course MS5031 --lecture 2
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from cognitive_flashcard_generator.content_orchestrator import ContentOrchestrator


def generate_flashcards(args):
    """Generate flashcards subcommand."""
    
    orchestrator = ContentOrchestrator(
        courses_json_path=args.courses_json,
        output_base_dir=args.output_dir
    )
    
    try:
        flashcards_path = orchestrator.generate_flashcards_for_lecture(
            course_id=args.course,
            lecture_number=args.lecture,
            min_cards_threshold=args.min_cards
        )
        
        print(f"\n{'#'*80}")
        print("# FLASHCARD GENERATION COMPLETE")
        print(f"# Output: {flashcards_path}")
        print(f"{'#'*80}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return 1


def generate_quizzes(args):
    """Generate quizzes subcommand."""
    
    orchestrator = ContentOrchestrator(
        courses_json_path=args.courses_json,
        output_base_dir=args.output_dir
    )
    
    try:
        quiz_paths = orchestrator.generate_quizzes_for_lecture(
            course_id=args.course,
            lecture_number=args.lecture
        )
        
        if quiz_paths:
            print(f"\n{'#'*80}")
            print("# QUIZ GENERATION COMPLETE")
            print(f"# Generated {len(quiz_paths)} quiz level(s)")
            for level, path in quiz_paths.items():
                print(f"#   {level}: {path}")
            print(f"{'#'*80}\n")
            return 0
        else:
            print("\n⚠️  No quizzes generated\n")
            return 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return 1


def generate_all(args):
    """Generate both flashcards and quizzes."""
    
    print(f"\n{'='*80}")
    print("GENERATING ALL LEARNING MATERIALS")
    print(f"Course: {args.course} | Lecture: {args.lecture}")
    print(f"{'='*80}\n")
    
    # Generate flashcards first
    print("STEP 1: Flashcards")
    print("-" * 80)
    flashcard_result = generate_flashcards(args)
    
    if flashcard_result != 0:
        print("\n⚠️  Flashcard generation failed. Skipping quiz generation.\n")
        return flashcard_result
    
    # Generate quizzes
    print("\nSTEP 2: Quizzes")
    print("-" * 80)
    quiz_result = generate_quizzes(args)
    
    if flashcard_result == 0 and quiz_result == 0:
        print(f"\n{'#'*80}")
        print("# ALL LEARNING MATERIALS GENERATED SUCCESSFULLY")
        print(f"# Course: {args.course} | Lecture: {args.lecture}")
        print(f"{'#'*80}\n")
    
    return max(flashcard_result, quiz_result)


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Generate learning materials (flashcards and quizzes) from course content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate flashcards only
  %(prog)s generate-flashcards --course MS5031 --lecture 2
  
  # Generate quizzes only
  %(prog)s generate-quizzes --course MS5031 --lecture 2
  
  # Generate both flashcards and quizzes
  %(prog)s generate-all --course MS5031 --lecture 2
        """
    )
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Common arguments for all subcommands
    def add_common_args(subparser):
        subparser.add_argument(
            '--course',
            required=True,
            help='Course ID (e.g., MS5031)'
        )
        subparser.add_argument(
            '--lecture',
            required=True,
            help='Lecture number (e.g., 2)'
        )
        subparser.add_argument(
            '--courses-json',
            default='courses_resources/courses.json',
            help='Path to courses.json file (default: courses_resources/courses.json)'
        )
        subparser.add_argument(
            '--output-dir',
            default='courses',
            help='Base output directory (default: courses)'
        )
    
    # Subcommand: generate-flashcards
    parser_flashcards = subparsers.add_parser(
        'generate-flashcards',
        help='Generate flashcards for a lecture'
    )
    add_common_args(parser_flashcards)
    parser_flashcards.add_argument(
        '--min-cards',
        type=int,
        default=5,
        help='Minimum number of cards expected (default: 5)'
    )
    parser_flashcards.set_defaults(func=generate_flashcards)
    
    # Subcommand: generate-quizzes
    parser_quizzes = subparsers.add_parser(
        'generate-quizzes',
        help='Generate quizzes for a lecture (requires existing flashcards)'
    )
    add_common_args(parser_quizzes)
    parser_quizzes.set_defaults(func=generate_quizzes)
    
    # Subcommand: generate-all
    parser_all = subparsers.add_parser(
        'generate-all',
        help='Generate both flashcards and quizzes (default)'
    )
    add_common_args(parser_all)
    parser_all.add_argument(
        '--min-cards',
        type=int,
        default=5,
        help='Minimum number of cards expected (default: 5)'
    )
    parser_all.set_defaults(func=generate_all)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no subcommand provided, default to generate-all
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the appropriate function
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

