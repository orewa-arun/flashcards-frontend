#!/usr/bin/env python3
"""
Script to create flashcards-only JSON files by removing recall_questions
from cognitive flashcard objects.

This script processes all *_cognitive_flashcards.json files in the courses/
directory and creates new *_cognitive_flashcards_only.json files containing
the same flashcard data but without the recall_questions field.
"""

import json
import os
import glob
from pathlib import Path


def find_cognitive_flashcard_files(courses_dir: str) -> list:
    """Find all *_cognitive_flashcards.json files in the courses directory."""
    pattern = os.path.join(courses_dir, "**", "*_cognitive_flashcards.json")
    return glob.glob(pattern, recursive=True)


def process_flashcard_file(file_path: str) -> None:
    """Process a single cognitive flashcard file and create the flashcards-only version."""
    print(f"Processing: {file_path}")

    # Load the original JSON data
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create a copy of the data structure
    flashcards_only_data = {
        "metadata": data["metadata"].copy(),
        "flashcards": []
    }

    # Process each flashcard, removing recall_questions
    for flashcard in data["flashcards"]:
        # Create a copy of the flashcard without recall_questions
        flashcard_copy = {}
        for key, value in flashcard.items():
            if key != "recall_questions":
                flashcard_copy[key] = value
        flashcards_only_data["flashcards"].append(flashcard_copy)

    # Create the output filename
    input_path = Path(file_path)
    output_filename = input_path.stem + "_only.json"
    output_path = input_path.with_name(output_filename)

    # Save the flashcards-only data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(flashcards_only_data, f, indent=2, ensure_ascii=False)

    print(f"Created: {output_path}")


def main():
    """Main function to process all cognitive flashcard files."""
    courses_dir = "courses"

    if not os.path.exists(courses_dir):
        print(f"Error: {courses_dir} directory not found!")
        return

    # Find all cognitive flashcard files
    flashcard_files = find_cognitive_flashcard_files(courses_dir)

    if not flashcard_files:
        print(f"No *_cognitive_flashcards.json files found in {courses_dir}")
        return

    print(f"Found {len(flashcard_files)} cognitive flashcard files to process:")
    for file_path in flashcard_files:
        print(f"  - {file_path}")

    print("\nProcessing files...")

    # Process each file
    for file_path in flashcard_files:
        try:
            process_flashcard_file(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print("\nDone! All flashcards-only files have been created.")


if __name__ == "__main__":
    main()
