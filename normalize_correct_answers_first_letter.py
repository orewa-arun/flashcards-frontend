#!/usr/bin/env python3
"""
Heuristic normalizer for `correct_answer` based on first-letter option labels.

Idea (your spec):
- Look at the **first letter** of the correct answer text.
- If it is A, B, C or D *followed by a space or punctuation* (e.g. "a ", "B:", "c)"),
  treat that as the option key.
- Normalize `correct_answer` to an array with the **capitalized letter**, e.g.:
    "b: create a new table ..."      -> ["B"]
    ["c this is long", "more text"] -> ["C"]

Scope:
- Scans all `quiz/*.json` files under the repo (backend courses, etc.).
- Only changes questions where:
  - `correct_answer` is a string or list, AND
  - the first element matches the "letter + space/punctuation" pattern,
  - AND that letter exists as an option key on the question (A–D).
- Already-normalized answers like ["A"], ["B"] are left untouched.

Usage (from repo root):
    python normalize_correct_answers_first_letter.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).parent

# Regex: first non-space char A–D/a–d followed by space or punctuation.
FIRST_LETTER_RE = re.compile(r"^\s*([a-dA-D])[\s:.\)\-\]]")

# Regex: patterns like "Option C" or "Approach D" anywhere in the text.
LABEL_LETTER_RE = re.compile(r"\b(?:option|approach)\s+([a-dA-D])\b")


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
    if isinstance(data, list):
        return data, data, "list"

    # Unexpected shape – return empty but keep data so we can log
    return [], data, "unknown"


def _extract_letter(value: Any) -> str | None:
    """
    Heuristically extract an option letter (A–D) from a `correct_answer` value.

    Heuristics (in order):
    1. **First-letter heuristic** (original idea):
       - Look at the first non-space character of the text.
       - If it's A–D followed by space/punctuation → use that as the key.
    2. **Label heuristic** for explanatory text:
       - If the text contains phrases like "Option C" or "Approach D",
         use that letter.

    For lists, we:
    - Use the **first element** for the first-letter heuristic.
    - Use the **joined list text** for the label heuristic (to catch
      multi-part explanations split across array elements).

    Returns:
        Uppercased letter (A–D) or None if no confident match.
    """
    # First-letter heuristic on the first element / string value
    first_text: str | None
    if isinstance(value, list) and value and isinstance(value[0], str):
        first_text = value[0]
    elif isinstance(value, str):
        first_text = value
    else:
        first_text = None

    if first_text:
        m = FIRST_LETTER_RE.match(first_text)
        if m:
            letter = m.group(1).upper()
            if letter in {"A", "B", "C", "D"}:
                return letter

    # Label heuristic on the full text (handles "Approach D ..." / "Option C ...")
    if isinstance(value, list):
        joined_text = " ".join(str(v or "") for v in value)
    else:
        joined_text = str(value or "")

    m2 = LABEL_LETTER_RE.search(joined_text)
    if m2:
        letter = m2.group(1).upper()
        if letter in {"A", "B", "C", "D"}:
            return letter

    return None


def normalize_quiz_file(quiz_path: Path) -> bool:
    """
    Normalize all `correct_answer` fields in a single quiz file using the
    first-letter heuristic.

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
        if "correct_answer" not in question or "options" not in question:
            continue

        original = question["correct_answer"]

        # Skip if already normalized like ["A"], ["B"]
        if isinstance(original, list) and len(original) == 1 and isinstance(original[0], str):
            if original[0] in {"A", "B", "C", "D"}:
                continue

        letter = _extract_letter(original)
        if not letter:
            continue

        # Only apply if this letter actually exists as an option key
        option_keys = set((question.get("options") or {}).keys())
        if letter not in option_keys:
            continue

        question["correct_answer"] = [letter]
        modified = True
        changes.append(f"Q{idx}: {repr(original)} -> ['{letter}']")

    if modified:
        with open(quiz_path, "w", encoding="utf-8") as f:
            json.dump(root_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Normalized (first-letter heuristic): {quiz_path}")
        for desc in changes[:5]:
            print(f"  - {desc}")
        if len(changes) > 5:
            print(f"  ... and {len(changes) - 5} more change(s)")
    else:
        print(f"✔ No changes needed (first-letter heuristic): {quiz_path}")

    return modified


def main() -> None:
    """
    Walk the repo and normalize all `quiz/*.json` files using the
    first-letter heuristic.
    """
    quiz_files: List[Path] = []

    for pattern in ["**/quiz/*.json"]:
        quiz_files.extend(ROOT.glob(pattern))

    quiz_files = sorted({p.resolve() for p in quiz_files})

    print(f"Found {len(quiz_files)} quiz files\n")

    modified_count = 0
    for path in quiz_files:
        if any(part in {"node_modules", ".git", ".venv"} for part in path.parts):
            continue
        if normalize_quiz_file(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} quiz file(s).")


if __name__ == "__main__":
    main()


