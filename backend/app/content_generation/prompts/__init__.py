"""Prompt templates for content generation."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(filename: str) -> str:
    """
    Load a prompt template from file.
    
    Args:
        filename: Name of the prompt file
        
    Returns:
        Prompt template content
    """
    prompt_path = PROMPTS_DIR / filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_flashcard_prompt() -> str:
    """Get the flashcard generation prompt template."""
    return load_prompt("intelligent_flashcard_only_prompt_v2.txt")


def get_quiz_prompt(level: int) -> str:
    """
    Get the quiz generation prompt for a specific level.
    
    Args:
        level: Quiz difficulty level (1-4)
        
    Returns:
        Quiz prompt template
    """
    if not 1 <= level <= 4:
        raise ValueError(f"Invalid level: {level}. Must be 1-4.")
    
    return load_prompt(f"level_{level}_quiz_prompt.txt")


def get_slide_analysis_prompt() -> str:
    """Get the slide analysis prompt template."""
    return load_prompt("content_analysis_prompt.txt")


def get_batch_slide_analysis_prompt(num_slides: int, course_context: str = "") -> str:
    """
    Get the batch slide analysis prompt template.
    
    Args:
        num_slides: Number of slides in the batch
        course_context: Formatted course context string
        
    Returns:
        Batch analysis prompt with placeholders replaced
    """
    prompt = load_prompt("batch_content_analysis_prompt.txt")
    prompt = prompt.replace("{NUM_SLIDES}", str(num_slides))
    prompt = prompt.replace("{COURSE_CONTEXT}", course_context)
    return prompt

