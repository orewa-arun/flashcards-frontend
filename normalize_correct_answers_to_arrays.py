#!/usr/bin/env python3
"""
Normalize `correct_answer` format in ALL `*_quiz.json` files.

Goals:
- Use **arrays of option KEYS** for every question, even when there is only one correct option.
  - MCQ:  ["C"]
  - MCA:  ["A", "C", "D"]
- For legacy data where `correct_answer` is stored as long text (or split across multiple
  strings) instead of option keys, **map it back to the correct option letter(s)** using
  the same normalization logic as the adaptive quiz backend:
  - Strip only the option label from the *option text* (e.g. "B: ..." → "…")
  - Keep the option keys themselves in **caps** ("A", "B", "C", "D")
  - Preserve arrays (e.g. multi-correct questions remain arrays of keys).

What this script does:
- Scans the entire repo for any `quiz/*.json` file
  (e.g. `backend/courses`, `courses`, `frontend/public/courses`, etc.).
- For each question with `options` and `correct_answer`:
  - Uses `AdaptiveQuizService._normalize_correct_answer` to convert the stored
    `correct_answer` into an array of option KEYS (["A"], ["B", "D"], etc.).
  - This includes handling messy cases like:
      ["B: Long text ...", "additional sentence", "final clause"]
    which will be normalized to ["B"].
- If the backend normalization cannot map the answer to option keys, the
  original value is left untouched but logged.

Usage (from repo root):
    source .venv/bin/activate
    python normalize_correct_answers_to_arrays.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).parent

# Ensure we can import backend services (AdaptiveQuizService) by putting
# the `backend` directory on sys.path.
BACKEND_DIR = ROOT / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.services.adaptive_quiz_service import AdaptiveQuizService
except Exception as e:  # pragma: no cover - import failure is reported at runtime
    AdaptiveQuizService = None  # type: ignore[assignment]
    print(f"⚠️  Warning: could not import AdaptiveQuizService: {e}")


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


def _normalize_correct_answer(question: Dict[str, Any]) -> Tuple[Any, str]:
    """
    Normalize `question["correct_answer"]` to an array of option KEYS, using the
    same normalization logic as the adaptive quiz backend.

    Returns:
        (normalized_value, description_of_change)
        If no change, description_of_change is "".
    """
    original = question.get("correct_answer")

    # If we couldn't import AdaptiveQuizService (e.g., script run outside full app
    # environment), fall back to a minimal array-only normalization.
    if AdaptiveQuizService is None:
        if isinstance(original, list):
            if not original:
                return original, "empty_list"
            return original, ""
        if isinstance(original, str):
            raw = original.strip()
            if not raw:
                return original, "empty_string"
            if "," in raw:
                parts = [part.strip() for part in raw.split(",") if part.strip()]
                if not parts:
                    return original, "empty_after_split"
                return parts, f'"{original}" -> {parts}'
            return [raw], f'"{original}" -> ["{raw}"]'
        return original, f"unsupported_type:{type(original).__name__}"

    # Use the backend's normalization, which:
    # - strips only the option label from option texts
    # - joins multi-part answers
    # - returns an array of option KEYS in caps.
    normalized = AdaptiveQuizService._normalize_correct_answer(question)

    if normalized == original:
        # No effective change
        return original, ""

    return normalized, "normalized_with_backend_logic"


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
        normalized, change_desc = _normalize_correct_answer(question)

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


