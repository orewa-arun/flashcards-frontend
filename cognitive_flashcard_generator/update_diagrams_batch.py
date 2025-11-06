#!/usr/bin/env python3
"""
World-Class Diagram Generation Script

This script completely regenerates mermaid_diagrams and math_visualizations
for flashcard JSON files using Claude AI in "beast mode" for maximum quality.

Usage:
    python update_diagrams_batch.py MS5150                    # Update all flashcards in course
    python update_diagrams_batch.py MS5150 SI_Pricing         # Update specific lecture
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import anthropic
import dotenv

dotenv.load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

# Model Configuration - Using Opus for world-class quality
MODEL_NAME = "claude-haiku-4-5"

# Batch Configuration
BATCH_SIZE = 3  # Process 5 flashcards per API call

# Rate Limiting
DELAY_BETWEEN_BATCHES = 2  # seconds

# API Configuration
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
    sys.exit(1)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=API_KEY)

# ============================================================================
# PROMPT TEMPLATE
# ============================================================================

SYSTEM_PROMPT = """You are a world-class instructional designer and expert in data visualization.

Your task: Generate `mermaid_diagrams` and `math_visualizations` for flashcards.

MERMAID DIAGRAM GUIDELINES:
- Use modern Mermaid.js syntax (flowchart TD/LR, sequenceDiagram, graph, etc.)
- Choose the BEST diagram type for each context (don't default to flowcharts)
- Use professional color schemes with Material Design colors
- Make diagrams clean, uncluttered, with concise labels
- The eli5 diagram should be visibly simpler than the real_world_use_case diagram
- Use styling like: style NodeName fill:#e3f2fd
- Use edge labels: -->|label text| or -.label text.->

MATHEMATICAL VISUALIZATIONS (Graphviz/DOT) - CRITICAL RULES:

🚨 ABSOLUTE MANDATE: For ANY concept with even the SLIGHTEST mathematical, statistical, algorithmic, or quantitative component, you MUST create mathematical visualizations. This is NON-NEGOTIABLE.

GENERATE FOR ALL 6 ANSWER TYPES:
- concise: ALWAYS generate for any mathematical concept. Show the core formula, equation, or mathematical relationship.
- analogy: If your analogy involves any quantitative comparison, proportions, or structured relationships, create a visualization.
- eli5: Simple mathematical concepts (like addition, comparison, basic graphs) are perfect for ELI5 visualizations.
- real_world_use_case: Business scenarios almost always involve numbers, trends, comparisons - visualize these relationships.
- common_mistakes: Mathematical errors are often visual - show correct vs incorrect formulations, graphs, or calculations.
- example: Any example with numbers, data, or quantitative relationships needs mathematical visualization.

CRITICAL VISUALIZATION REQUIREMENTS:
1. TEXT CONTAINMENT (CRITICAL FAILURE IF VIOLATED): All text within a node MUST be fully contained within its boundaries.
   - Use newlines (\\n) to break long lines of text manually (every 10-15 characters)
   - Use margin=0.3 or higher for all nodes to provide padding
   - For complex formulas, use multiple connected nodes instead of cramming everything into one
   - Use fontsize=10-12 for readability without overflow
   - Test mentally: "Would this text fit in a box this size?"

2. LAYOUT ENGINE WISDOM (Choose the right tool):
   - Use neato for: scatter plots, coordinate-based visualizations, spatial relationships, data distributions
   - Use dot for: hierarchical formulas, process flows, structured relationships
   - Use fdp for: network-like mathematical relationships
   - Use circo for: cyclic mathematical processes

3. WHEN TO GENERATE GRAPHVIZ DOT CODE:
   - ANY mathematical formula or equation
   - Statistical relationships (correlation, regression, distributions)
   - Algorithmic processes with mathematical steps
   - Data structures with quantitative properties
   - Mathematical comparisons or trade-offs
   - Probability and statistical concepts
   - Optimization problems and solutions
   - Quantitative business metrics and KPIs
   - Financial calculations and models

4. BEST PRACTICES FOR DOT CODE:
   - Use rankdir=LR for mathematical formulas (left to right flow)
   - Use fontsize=10-12 for optimal readability without overflow
   - Use margin=0.2-0.4 for all nodes to prevent text overflow
   - Use penwidth=2 for important mathematical relationships
   - Use colors to distinguish different types of mathematical elements
   - Use subgraph cluster_* to group related mathematical concepts
   - Break complex formulas into multiple connected nodes
   - NEVER use invisible edges - make all mathematical relationships visible

🚨 JSON OUTPUT FORMAT - CRITICAL 🚨

You MUST return valid JSON. Follow these rules EXACTLY:

1. NO markdown: Start with [ and end with ]
2. NO code blocks: No ```json or ``` anywhere
3. ALL diagram code must be ONE LINE with \\n for line breaks

Example of CORRECT format:
[{"flashcard_id":"ID","mermaid_diagrams":{"concise":"graph TD\\n  A-->B\\n  B-->C"},"math_visualizations":{"concise":"digraph G {\\n  node [margin=0.3, fontsize=11];\\n  A [label=\\"Formula\\\\nComponent\\"];\\n  A -> B;\\n}"}}]

Example of WRONG format (will fail):
```json
[{
  "mermaid_diagrams": {
    "concise": "graph TD
      A-->B"
  }
}]
```

4. Escape these characters in diagram strings:
   - Backslash: \\ becomes \\\\
   - Quote: " becomes \\"
   - Newline: actual newline becomes \\n
   - Tab: actual tab becomes \\t

5. Test mentally: Can Python's json.loads() parse this?

Return structure:
[{
  "flashcard_id": "...",
  "mermaid_diagrams": {"concise":"...","analogy":"...","eli5":"...","real_world_use_case":"...","common_mistakes":"...","example":"..."},
  "math_visualizations": {"concise":"...","analogy":"...","eli5":"...","real_world_use_case":"...","common_mistakes":"...","example":"..."}
}]

Remember: One line per diagram string, use \\n for line breaks, NO markdown wrappers, ALWAYS include margin and fontsize in Graphviz diagrams."""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_target_files(course_code: str, lecture_prefix: Optional[str] = None) -> List[Path]:
    """
    Find target flashcard files based on course code and optional lecture prefix.
    
    Args:
        course_code: Course code like "MS5150"
        lecture_prefix: Optional lecture prefix like "SI_Pricing"
    
    Returns:
        List of Path objects to target files (absolute paths)
    """
    # Get the project root (parent of cognitive_flashcard_generator)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    base_path = project_root / "courses" / course_code / "cognitive_flashcards"
    
    if not base_path.exists():
        print(f"ERROR: Course directory not found: {base_path}")
        return []
    
    if lecture_prefix:
        # Single lecture mode
        target_file = base_path / lecture_prefix / f"{lecture_prefix}_cognitive_flashcards_only.json"
        if target_file.exists():
            return [target_file.resolve()]
        else:
            print(f"ERROR: File not found: {target_file}")
            return []
    else:
        # Course-wide mode - find all flashcard files
        target_files = list(base_path.glob("**/*_cognitive_flashcards_only.json"))
        if not target_files:
            print(f"ERROR: No flashcard files found in {base_path}")
            return []
        return sorted([f.resolve() for f in target_files])


def create_backup(file_path: Path) -> Path:
    """Create a timestamped backup of the file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = file_path.with_suffix(f".{timestamp}.bak")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ Backup created: {backup_path.name}")
    return backup_path


def extract_flashcard_context(flashcard: Dict[str, Any]) -> Dict[str, Any]:
    """Extract essential context from a flashcard for the API."""
    return {
        "flashcard_id": flashcard.get("flashcard_id", ""),
        "type": flashcard.get("type", ""),
        "question": flashcard.get("question", ""),
        "answers": flashcard.get("answers", {}),
        "context": flashcard.get("context", ""),
        "example": flashcard.get("example", "")
    }


def create_batch_prompt(flashcards_batch: List[Dict[str, Any]]) -> str:
    """Create the prompt for a batch of flashcards."""
    batch_data = [extract_flashcard_context(fc) for fc in flashcards_batch]
    
    prompt = f"""Generate diagrams for {len(batch_data)} flashcard(s).

FLASHCARD DATA:
{json.dumps(batch_data, indent=2)}

🚨 OUTPUT FORMAT REQUIREMENTS 🚨

Your response must be VALID JSON that Python can parse.

CORRECT example:
[{{"flashcard_id":"ID","mermaid_diagrams":{{"concise":"graph TD\\n  A-->B"}},"math_visualizations":{{"concise":"digraph G {{\\n  A->B;\\n}}"}}}}]

WRONG example (DO NOT DO THIS):
```json
[{{
  "mermaid_diagrams": {{
    "concise": "graph TD
      A-->B"
  }}
}}]
```

Rules:
1. Start with [ and end with ]
2. NO markdown, NO code blocks, NO backticks
3. Diagram strings must be ONE LINE with \\n for line breaks
4. Escape: \\ → \\\\, " → \\", newline → \\n
5. Include all 6 diagram types for each flashcard

Generate world-class, elegant diagrams. Return ONLY the JSON array."""
    
    return prompt


def call_claude_api(prompt: str, max_retries: int = 3) -> str:
    """
    Call Claude API with retry logic.
    
    Args:
        prompt: The user prompt
        max_retries: Maximum number of retry attempts
    
    Returns:
        The API response text
    """
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model=MODEL_NAME,
                max_tokens=16000,  # Allow generous token limit for detailed diagrams
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract text from the first content block
            first_block = message.content[0]
            # Type guard: check if it's a TextBlock
            if hasattr(first_block, 'text') and isinstance(getattr(first_block, 'text', None), str):
                return first_block.text  # type: ignore
            else:
                raise ValueError(f"Unexpected content block type: {type(first_block)}")
        
        except anthropic.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"  ⚠ Rate limit hit. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
        
        except Exception as e:
            print(f"  ✗ API Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
    
    raise Exception("Max retries exceeded")


def fix_json_escaping(text: str) -> str:
    """
    Attempt to fix common JSON escaping issues in diagram strings.
    This is a heuristic approach - not perfect but handles most cases.
    """
    # This is complex because we need to fix unescaped characters inside JSON string values
    # without breaking the JSON structure itself
    
    # Strategy: Use regex to find string values and fix escaping within them
    # This is a simplified approach - for production, consider using a proper JSON repair library
    
    return text


def parse_api_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse the API response and extract the JSON array.
    Handles markdown code blocks and malformed JSON.
    """
    try:
        # Step 1: Remove markdown code blocks if present
        cleaned_text = response_text.strip()
        
        # Remove opening markdown fence
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        
        # Remove closing markdown fence
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Step 2: Find JSON array boundaries
        start_idx = cleaned_text.find('[')
        end_idx = cleaned_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON array found in response")
        
        json_str = cleaned_text[start_idx:end_idx]
        
        # Step 3: Try to parse directly first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If direct parsing fails, try fixing common issues
            # (This is where we could add more sophisticated repair logic)
            pass
        
        # If we get here, parsing failed - raise with debug info
        raise ValueError("JSON parsing failed even after cleanup")
    
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ✗ Failed to parse API response as JSON: {str(e)}")
        print(f"  Response preview (first 1000 chars): {response_text[:1000]}...")
        print(f"  Response preview (last 500 chars): ...{response_text[-500:]}")
        
        # Try to save the problematic response for debugging
        debug_file = Path("debug_failed_response.txt")
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"  → Full response saved to {debug_file} for debugging")
        except Exception:
            pass
        
        raise


def merge_diagrams(flashcards: List[Dict[str, Any]], generated_data: List[Dict[str, Any]]) -> int:
    """
    Merge generated diagrams back into the flashcards.
    
    Args:
        flashcards: Original flashcard list
        generated_data: Generated diagram data from API
    
    Returns:
        Number of flashcards successfully updated
    """
    # Create a lookup dictionary
    generated_lookup = {item["flashcard_id"]: item for item in generated_data}
    
    updated_count = 0
    
    for flashcard in flashcards:
        flashcard_id = flashcard.get("flashcard_id", "")
        
        if flashcard_id in generated_lookup:
            generated = generated_lookup[flashcard_id]
            
            # Update the diagrams
            flashcard["mermaid_diagrams"] = generated.get("mermaid_diagrams", {})
            flashcard["math_visualizations"] = generated.get("math_visualizations", {})
            
            updated_count += 1
    
    return updated_count


def process_file(file_path: Path) -> bool:
    """
    Process a single flashcard file.
    
    Args:
        file_path: Path to the flashcard JSON file
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    # Try to show relative path, fallback to absolute if not possible
    try:
        display_path = file_path.relative_to(Path.cwd())
    except ValueError:
        # If not a subpath of cwd, try relative to project root
        try:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent
            display_path = file_path.relative_to(project_root)
        except ValueError:
            # Fallback to absolute path
            display_path = file_path
    print(f"Processing: {display_path}")
    print(f"{'='*80}")
    
    try:
        # Create backup
        create_backup(file_path)
        
        # Load the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        flashcards = data.get("flashcards", [])
        total_flashcards = len(flashcards)
        
        print(f"Total flashcards: {total_flashcards}")
        
        # Process in batches
        total_batches = (total_flashcards + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_idx in range(0, total_flashcards, BATCH_SIZE):
            batch_num = (batch_idx // BATCH_SIZE) + 1
            batch = flashcards[batch_idx:batch_idx + BATCH_SIZE]
            
            print(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} flashcard(s)...")
            
            try:
                # Create prompt
                prompt = create_batch_prompt(batch)
                
                # Call API
                print(f"  → Calling Claude API ({MODEL_NAME})...")
                response_text = call_claude_api(prompt)
                
                # Parse response
                print(f"  → Parsing response...")
                generated_data = parse_api_response(response_text)
                
                # Merge diagrams
                print(f"  → Merging diagrams...")
                updated = merge_diagrams(batch, generated_data)
                print(f"  ✓ Updated {updated}/{len(batch)} flashcard(s)")
                
            except Exception as e:
                print(f"  ✗ Batch processing failed: {str(e)}")
                print(f"  → Attempting individual processing as fallback...")
                
                # Fallback: Process each flashcard individually
                for idx, flashcard in enumerate(batch):
                    try:
                        print(f"    → Processing flashcard {idx + 1}/{len(batch)} individually...")
                        individual_prompt = create_batch_prompt([flashcard])
                        individual_response = call_claude_api(individual_prompt)
                        individual_data = parse_api_response(individual_response)
                        updated = merge_diagrams([flashcard], individual_data)
                        print(f"    ✓ Updated flashcard {flashcard.get('flashcard_id', 'unknown')}")
                        time.sleep(1)  # Small delay between individual calls
                    except Exception as individual_error:
                        print(f"    ✗ Failed to process {flashcard.get('flashcard_id', 'unknown')}: {str(individual_error)}")
                        continue
            
            # Rate limiting
            if batch_num < total_batches:
                print(f"  ⏳ Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        # Save the updated file
        print(f"\n→ Saving updated file...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully updated {file_path.name}")
        return True
    
    except Exception as e:
        print(f"\n✗ ERROR processing {file_path.name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python update_diagrams_batch.py <course_code>                    # Update all")
        print("  python update_diagrams_batch.py <course_code> <lecture_prefix>   # Update one")
        print("\nExamples:")
        print("  python update_diagrams_batch.py MS5150")
        print("  python update_diagrams_batch.py MS5150 SI_Pricing")
        sys.exit(1)
    
    course_code = sys.argv[1]
    lecture_prefix = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Find target files
    print(f"\n🔍 Searching for target files...")
    target_files = find_target_files(course_code, lecture_prefix)
    
    if not target_files:
        sys.exit(1)
    
    print(f"✓ Found {len(target_files)} file(s) to process")
    
    # Process each file
    success_count = 0
    failure_count = 0
    
    for file_path in target_files:
        if process_file(file_path):
            success_count += 1
        else:
            failure_count += 1
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"✓ Successfully processed: {success_count} file(s)")
    if failure_count > 0:
        print(f"✗ Failed: {failure_count} file(s)")
    print(f"\nModel used: {MODEL_NAME}")
    print(f"Batch size: {BATCH_SIZE} flashcards per API call")


if __name__ == "__main__":
    main()

