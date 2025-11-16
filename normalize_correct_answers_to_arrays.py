#!/usr/bin/env python3
"""
Normalize `correct_answer` format in ALL `*_quiz.json` files.

Goal:
- Use **arrays for every question**, even when there is only one correct option.
  - MCQ:  ["C"]
  - MCA:  ["A", "C", "D"]

Why:
- Prompts and backend now expect arrays for both MCQ and MCA.
- Some quiz files still have legacy formats like "C" or "A,B,C".

What this script does:
- Scans the entire repo for any `quiz/*.json` file
  (e.g. `backend/courses`, `courses`, `frontend/public/courses`, etc.).
- For each question:
  - If `correct_answer` is a string:
      "C"       -> ["C"]
      "A,B,C"   -> ["A", "B", "C"]
  - If it's already a list: keeps it as-is (unless empty, which is logged).
  - Any other type is logged and left untouched.

Usage (from repo root):
    source .venv/bin/activate
    python normalize_correct_answers_to_arrays.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).parent


def _load_questions(quiz_path: Path) -> Tuple[List[Dict[str, Any]], Any, str]:
    """
    Load questions from a quiz file.

    Returns:
        questions: list of question dicts
        root_data: original JSON root (list or dict)
        mode: "wrapped" if data["questions"], "list" if root is list, or "unknown"
    """
    with open(quiz_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "questions" in data:
        return data["questions"], data, "wrapped"
    elif isinstance(data, list):
        return data, data, "list"
    else:
        # Unexpected shape – return empty but keep data so we can log
        return [], data, "unknown"


def _normalize_correct_answer(value: Any) -> Tuple[Any, str]:
    """
    Normalize a single correct_answer value to an array form.

    Returns:
        (normalized_value, description_of_change)
        If no change, description_of_change is "".
    """
    # Already a non-empty list -> keep as-is
    if isinstance(value, list):
        if not value:
            return value, "empty_list"
        return value, ""

    # String formats
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return value, "empty_string"

        # Comma-separated -> split to array
        if "," in raw:
            parts = [part.strip() for part in raw.split(",") if part.strip()]
            if not parts:
                return value, "empty_after_split"
            return parts, f'"{value}" -> {parts}'

        # Single token -> single-element array
        return [raw], f'"{value}" -> ["{raw}"]'

    # Any other type – leave untouched but mark
    return value, f"unsupported_type:{type(value).__name__}"


def normalize_quiz_file(quiz_path: Path) -> bool:
    """
    Normalize all `correct_answer` fields in a single quiz file.

    Returns:
        True if file was modified, False otherwise.
    """
    questions, root_data, mode = _load_questions(quiz_path)

    if mode == "unknown":
        print(f"⚠️  Skipping {quiz_path} - unexpected JSON structure")
        return False

    modified = False
    changes: List[str] = []

    for idx, question in enumerate(questions, start=1):
        if "correct_answer" not in question:
            continue

        original = question["correct_answer"]
        normalized, change_desc = _normalize_correct_answer(original)

        if change_desc and not change_desc.startswith("unsupported_type"):
            question["correct_answer"] = normalized
            modified = True
            changes.append(f"Q{idx}: {change_desc}")
        elif change_desc.startswith("unsupported_type"):
            changes.append(f"Q{idx}: {change_desc}")

    if modified:
        # Write back in the same shape
        with open(quiz_path, "w", encoding="utf-8") as f:
            json.dump(root_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Normalized {quiz_path}")
        for desc in changes[:5]:
            print(f"  - {desc}")
        if len(changes) > 5:
            print(f"  ... and {len(changes) - 5} more change(s)")
    else:
        print(f"✔ Already normalized: {quiz_path}")

    return modified


def main() -> None:
    """
    Walk the repo and normalize all `quiz/*.json` files:
    - backend/courses/**/quiz/*.json
    - courses/**/quiz/*.json
    - frontend/public/**/quiz/*.json
    """
    quiz_files: List[Path] = []

    # Search all quiz directories under repo
    for pattern in ["**/quiz/*.json"]:
        quiz_files.extend(ROOT.glob(pattern))

    # De-duplicate & sort
    quiz_files = sorted({p.resolve() for p in quiz_files})

    print(f"Found {len(quiz_files)} quiz files\n")

    modified_count = 0
    for path in quiz_files:
        # Skip obvious non-course dirs if needed (e.g., node_modules)
        if any(part in {"node_modules", ".git", ".venv"} for part in path.parts):
            continue
        if normalize_quiz_file(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} quiz file(s).")


if __name__ == "__main__":
    main()


