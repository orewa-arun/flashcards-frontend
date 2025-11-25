# Prompts Usage Guide

Complete guide to all prompt templates and their usage in the content generation pipeline.

---

## 📋 Table of Contents

1. [Active Prompts (Currently Used)](#active-prompts)
2. [Available Prompts (Not Yet Integrated)](#available-prompts)
3. [Prompt Integration Points](#prompt-integration-points)

---

## 🟢 Active Prompts (Currently Used)

These prompts are actively used in the current implementation:

### 1. `content_analysis_prompt.txt`

**Purpose**: Basic slide content analysis

**Used By**: `analyzers/slide_analyzer.py` → `SlideAnalyzer.analyze_slide()`

**What It Does**:
- Analyzes individual slide images
- Extracts key information from slides
- Returns structured JSON with title, topics, difficulty, prerequisites, formulas

**Output Format**:
```json
{
  "title": "Main topic",
  "topics": ["topic1", "topic2"],
  "difficulty_level": "beginner|intermediate|advanced",
  "prerequisites": ["concept1", "concept2"],
  "key_formulas": ["formula1", "formula2"]
}
```

**Status**: ✅ Currently used for slide-by-slide analysis

---

### 2. `intelligent_flashcard_only_prompt_v2.txt`

**Purpose**: Generate cognitive flashcards from structured content

**Used By**: `generators/flashcard_generator.py` → `FlashcardGenerator.generate()`

**What It Does**:
- Generates high-quality cognitive flashcards
- Creates flashcards with 5 types of answers (concise, analogy, ELI5, real-world use case, common mistakes)
- Includes relevance scores (1-10)
- Supports Mermaid.js diagrams and Graphviz visualizations
- **Hard limit: 5-6 flashcards per chunk** (prevents JSON truncation)

**Key Features**:
- Content adherence policy (only from provided content)
- Multi-faceted understanding approach
- Exam relevance scoring
- Visual diagram support

**Output Format**:
```json
[
  {
    "question": "What is MIS?",
    "concise": "Brief answer",
    "analogy": "Analogy explanation",
    "eli5": "Simple explanation",
    "real_world_use_case": "Practical example",
    "common_mistakes": "Common errors",
    "example": "Detailed example",
    "relevance_score": 9,
    "diagrams": ["mermaid code"]
  }
]
```

**Status**: ✅ Currently used for flashcard generation

---

### 3. `level_1_quiz_prompt.txt`

**Purpose**: Generate Level 1 (Foundation) quiz questions

**Used By**: `generators/quiz_generator.py` → `QuizGenerator.generate(level=1)`

**What It Does**:
- Generates foundation-level questions
- Tests basic recall and understanding
- 95% MCQ, 5% MCA questions
- Single concept, direct application
- 30-45 seconds to solve
- 70-80% pass rate target

**Difficulty Characteristics**:
- Cognitive Load: Single concept
- Scenario Complexity: 1-2 sentences
- Data Points: ≤ 3 pieces of information
- Reasoning Steps: 1 step

**Status**: ✅ Currently used for Level 1 quiz generation

---

### 4. `level_2_quiz_prompt.txt`

**Purpose**: Generate Level 2 (Intermediate) quiz questions

**Used By**: `generators/quiz_generator.py` → `QuizGenerator.generate(level=2)`

**What It Does**:
- Generates intermediate-level questions
- Tests application and analysis
- More complex scenarios than Level 1
- Requires connecting concepts

**Difficulty Characteristics**:
- More complex than Level 1
- Requires deeper understanding
- Multi-step reasoning

**Status**: ✅ Currently used for Level 2 quiz generation

---

### 5. `level_3_quiz_prompt.txt`

**Purpose**: Generate Level 3 (Advanced) quiz questions

**Used By**: `generators/quiz_generator.py` → `QuizGenerator.generate(level=3)`

**What It Does**:
- Generates advanced-level questions
- Tests synthesis and evaluation
- Complex scenarios
- Requires critical thinking

**Difficulty Characteristics**:
- Higher cognitive load
- Complex scenarios
- Multi-step reasoning

**Status**: ✅ Currently used for Level 3 quiz generation

---

### 6. `level_4_quiz_prompt.txt`

**Purpose**: Generate Level 4 (Expert) quiz questions

**Used By**: `generators/quiz_generator.py` → `QuizGenerator.generate(level=4)`

**What It Does**:
- Generates expert-level questions
- Tests deep understanding and critical thinking
- Most challenging questions
- Requires expert-level knowledge

**Difficulty Characteristics**:
- Highest cognitive load
- Most complex scenarios
- Expert-level reasoning

**Status**: ✅ Currently used for Level 4 quiz generation

---

## 🟡 Available Prompts (Not Yet Integrated)

These prompts exist but are not currently integrated into the pipeline:

### 7. `intelligent_flashcard_prompt_with_recall_questions.txt`

**Purpose**: Generate flashcards WITH embedded recall questions

**What It Does**:
- Similar to `intelligent_flashcard_only_prompt_v2.txt`
- **Additional feature**: Includes exactly 5 recall questions per flashcard
- More comprehensive than the "only" version

**Key Difference from v2**:
- Includes recall questions (5 per flashcard)
- More comprehensive testing capability
- Better for spaced repetition systems

**Potential Use Case**:
- Alternative flashcard generation mode
- When you want flashcards with built-in questions
- For more interactive learning experiences

**Status**: ⚠️ Available but not integrated

**Integration Point**: Could be added as an alternative in `FlashcardGenerator`

---

### 8. `hard_questions_prompt.txt`

**Purpose**: Generate challenging, tricky questions for advanced testing

**What It Does**:
- Creates HARD, TRICKY questions
- Tests deep understanding and critical thinking
- Significantly more difficult than typical recall questions
- Tests Bloom's Taxonomy higher levels (application, analysis, synthesis, evaluation)

**Question Type Distribution**:
- 40% scenario_mcq (scenario-based multiple choice)
- 20% sequencing (order steps/events)
- 20% categorization (classify items)
- 10% matching (match terms with definitions)
- 10% mcq (standard multiple choice)

**Key Features**:
- Includes tricky distractors
- Scenario-based questions
- Multi-step reasoning
- Filters out title/thank you slides

**Potential Use Case**:
- Generate "hard mode" questions
- Create exam-level challenging questions
- Test expert understanding
- Could be used as Level 5 or "Expert Mode"

**Status**: ⚠️ Available but not integrated

**Integration Point**: Could be added as Level 5 or alternative quiz generation mode

---

### 9. `textbook_content_synthesis_prompt.txt`

**Purpose**: Generate comprehensive textbook-aligned content

**What It Does**:
- Creates detailed educational content aligned with specific textbooks
- Generates content that could replace 3-5 lecture slides
- Emphasizes practical business applications
- Maintains academic rigor

**Output Structure**:
- Core Definition
- Key Concepts
- Practical Applications
- Examples
- Common Pitfalls
- Related Concepts

**Potential Use Case**:
- Enriching lecture content with textbook material
- Creating supplementary content
- Textbook integration features
- Content synthesis from multiple sources

**Status**: ⚠️ Available but not integrated

**Integration Point**: Could be used in content enrichment or synthesis features

---

### 10. `textbook_content_batch_synthesis_prompt.txt`

**Purpose**: Batch synthesis of multiple topics from textbooks

**What It Does**:
- Similar to `textbook_content_synthesis_prompt.txt`
- Designed for processing multiple topics at once
- Batch processing optimization
- Maintains consistency across topics

**Potential Use Case**:
- Processing entire chapters
- Bulk content generation
- Textbook-to-content conversion
- Large-scale content synthesis

**Status**: ⚠️ Available but not integrated

**Integration Point**: Could be used for batch processing features

---

## 🔗 Prompt Integration Points

### Current Integration Flow

```
1. Slide Analysis
   └─> content_analysis_prompt.txt
       (via SlideAnalyzer)

2. Flashcard Generation
   └─> intelligent_flashcard_only_prompt_v2.txt
       (via FlashcardGenerator)

3. Quiz Generation
   ├─> level_1_quiz_prompt.txt (Level 1)
   ├─> level_2_quiz_prompt.txt (Level 2)
   ├─> level_3_quiz_prompt.txt (Level 3)
   └─> level_4_quiz_prompt.txt (Level 4)
       (via QuizGenerator)
```

### Code References

**Slide Analysis**:
```python
# analyzers/slide_analyzer.py
from app.content_generation.prompts import get_slide_analysis_prompt
prompt = get_slide_analysis_prompt()
```

**Flashcard Generation**:
```python
# generators/flashcard_generator.py
from app.content_generation.prompts import get_flashcard_prompt
prompt = get_flashcard_prompt()
```

**Quiz Generation**:
```python
# generators/quiz_generator.py
from app.content_generation.prompts import get_quiz_prompt
prompt = get_quiz_prompt(level=1)  # or 2, 3, 4
```

---

## 📊 Prompt Usage Summary

| Prompt File | Status | Used In | Purpose |
|------------|--------|---------|---------|
| `content_analysis_prompt.txt` | ✅ Active | SlideAnalyzer | Basic slide analysis |
| `intelligent_flashcard_only_prompt_v2.txt` | ✅ Active | FlashcardGenerator | Cognitive flashcards |
| `level_1_quiz_prompt.txt` | ✅ Active | QuizGenerator | Foundation questions |
| `level_2_quiz_prompt.txt` | ✅ Active | QuizGenerator | Intermediate questions |
| `level_3_quiz_prompt.txt` | ✅ Active | QuizGenerator | Advanced questions |
| `level_4_quiz_prompt.txt` | ✅ Active | QuizGenerator | Expert questions |
| `intelligent_flashcard_prompt_with_recall_questions.txt` | ⚠️ Available | - | Flashcards with questions |
| `hard_questions_prompt.txt` | ⚠️ Available | - | Challenging questions |
| `textbook_content_synthesis_prompt.txt` | ⚠️ Available | - | Textbook content synthesis |
| `textbook_content_batch_synthesis_prompt.txt` | ⚠️ Available | - | Batch textbook synthesis |

---

## 🚀 Future Integration Opportunities

### 1. Flashcard with Recall Questions
- **Prompt**: `intelligent_flashcard_prompt_with_recall_questions.txt`
- **Use Case**: Alternative flashcard mode with embedded questions
- **Integration**: Add option to `FlashcardGenerator` to use this prompt

### 2. Hard Questions Mode
- **Prompt**: `hard_questions_prompt.txt`
- **Use Case**: Generate challenging exam-level questions
- **Integration**: Add as Level 5 or "Hard Mode" to `QuizGenerator`

### 3. Textbook Enrichment
- **Prompts**: `textbook_content_synthesis_prompt.txt`, `textbook_content_batch_synthesis_prompt.txt`
- **Use Case**: Enrich lecture content with textbook material
- **Integration**: New service for content enrichment

---

## 📝 Notes

- All prompts use placeholder variables like `{{COURSE_NAME}}` and `{{TEXTBOOK_REFERENCE}}`
- Prompts are loaded dynamically via `prompts/__init__.py` helper functions
- The current implementation focuses on the core pipeline (analysis → flashcards → quizzes)
- Additional prompts can be integrated as new features are added

---

## 🔧 Adding New Prompts

To add a new prompt:

1. Add the `.txt` file to `backend/app/content_generation/prompts/`
2. Add a helper function in `prompts/__init__.py`:
   ```python
   def get_new_prompt() -> str:
       return load_prompt("new_prompt.txt")
   ```
3. Use it in your generator/analyzer:
   ```python
   from app.content_generation.prompts import get_new_prompt
   prompt = get_new_prompt()
   ```

