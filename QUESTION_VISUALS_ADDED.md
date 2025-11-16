# QUESTION VISUALS ADDED TO ALL QUIZ LEVELS

## What Was Missing

Previously, the prompts only supported diagrams **in explanations**. Questions themselves couldn't include visuals, which is a critical limitation for many types of questions.

**Problem Examples:**
- Can't show a residual plot and ask "What pattern is this?"
- Can't show a formula and ask "What does this represent?"
- Can't show a process diagram and ask "What happens next?"
- Can't show data and ask students to interpret it

**Solution:**
Added `question_visual` and `question_visual_type` fields to all 4 quiz levels, with clear guidance on when and how to use them.

---

## Output Format (All Levels)

### Fields Added:

```json
{
  "type": "mcq",
  "question_text": "...",
  "question_visual": {
    "type": "matplotlib",
    "plot_type": "scatter_regression",
    "params": {
      "x": [1, 2, 3, 4, 5],
      "y": [2.1, 3.9, 6.2, 7.8, 10.1],
      "title": "Sales vs. Advertising Spend"
    }
  },
  "question_visual_type": "matplotlib",
  "options": { ... },
  "correct_answer": ["A"],
  "explanation": { ... }
}
```

**When no visual is needed:**
```json
{
  "question_visual": null,
  "question_visual_type": "None"
}
```

---

## When to Include question_visual (by Level)

### Level 1: Basic Understanding
- **ALWAYS** when the question requires interpreting a visual (e.g., "What pattern does this plot show?")
- **ALWAYS** when showing a formula/expression that's part of the question (use LaTeX)
- **WHEN HELPFUL** to provide context (e.g., showing a dataset structure)
- **Use `null` or omit** if the question is purely text-based

### Level 2: Application
- **ALWAYS** when testing application on visual data (e.g., "Given this scatter plot, what does the pattern suggest?")
- **ALWAYS** when the question requires interpreting a diagram to apply a concept
- **WHEN HELPFUL** to provide realistic context (e.g., showing actual data for a business scenario)
- **Use `null` or omit** if the question tests application through text alone

### Level 3: Analysis
- **ALWAYS** when the visual contains a subtle pattern or trap (e.g., "This plot looks normal, but...")
- **ALWAYS** when testing analysis of visual data with hidden complexities
- **WHEN HELPFUL** to set up a tricky scenario that requires careful interpretation
- **Use `null` or omit** if the trick is conceptual and doesn't require visual analysis

### Level 4: Synthesis
- **ALWAYS** when showing complex scenarios requiring synthesis of multiple visual elements
- **ALWAYS** when testing strategic decision-making based on visual evidence
- **WHEN HELPFUL** to show interactions between multiple concepts visually
- **Use `null` or omit** if the synthesis is purely conceptual

---

## Visual Type Rules for Questions (Generic for All Courses)

These rules are **course-agnostic** and work for any subject:

### Data Visualization → `matplotlib`
- **Use for:** Charts, graphs, plots for any numeric/statistical data
- **Examples:**
  - Scatter plots (regression, correlation)
  - Distributions (histograms, probability curves)
  - Time series plots
  - Bar charts, box plots
  - Residual plots, diagnostic plots
  - Any visual showing actual data patterns

### Mathematical Notation → `latex`
- **Use for:** Equations, formulas, expressions
- **Examples:**
  - Formulas to interpret: "What does this represent?"
  - Equations with blanks: "Fill in the missing term"
  - Complex expressions: "Simplify this"
  - Mathematical notation that's part of the question

### Process Flows / Hierarchies → `mermaid` or `graphviz`
- **Use for:** Flowcharts, decision trees, concept maps, system architectures
- **Examples:**
  - Decision trees: "What's the next step?"
  - Process flows: "Which path leads to X?"
  - Concept hierarchies: "Where does this fit?"
  - System diagrams: "What component is missing?"

### Tabular Data / Code
- **Use for:** Tables, datasets, code snippets
- **Include in** `question_text` as formatted text
- **Examples:**
  - Data tables: "Given this dataset..."
  - Code snippets: "What does this function return?"
  - Structured scenarios

---

## Course-Specific Examples

### Data Analytics Course:
```json
{
  "question_text": "What assumption is violated in this residual plot?",
  "question_visual": {
    "type": "matplotlib",
    "plot_type": "residual_plot",
    "params": {
      "fitted_values": [10, 20, 30, 40, 50],
      "residuals": [0.5, 1.2, 2.8, 5.1, 8.3],
      "title": "Residual Plot for Model A"
    }
  },
  "question_visual_type": "matplotlib"
}
```

### Machine Learning Course:
```json
{
  "question_text": "Which activation function is shown?",
  "question_visual": {
    "type": "matplotlib",
    "plot_type": "line_plot",
    "params": {
      "x": [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
      "y": [0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5],
      "title": "Activation Function Plot"
    }
  },
  "question_visual_type": "matplotlib"
}
```

### Calculus Course:
```json
{
  "question_text": "What is the derivative of this function?",
  "question_visual": {
    "type": "latex",
    "expression": "f(x) = 3x^2 + 2x - 5"
  },
  "question_visual_type": "latex"
}
```

### Software Engineering Course:
```json
{
  "question_text": "What design pattern is shown in this class diagram?",
  "question_visual": {
    "type": "mermaid",
    "code": "classDiagram\n    Subject <|-- ConcreteSubject\n    Observer <|-- ConcreteObserver\n    Subject : +attach(Observer)\n    Subject : +notify()"
  },
  "question_visual_type": "mermaid"
}
```

### Business Analytics Course:
```json
{
  "question_text": "Given this sales funnel, what's the conversion rate from leads to customers?",
  "question_visual": {
    "type": "graphviz",
    "code": "digraph G {\n    Leads [label=\"1000 Leads\"];\n    Qualified [label=\"500 Qualified\"];\n    Opportunities [label=\"200 Opportunities\"];\n    Customers [label=\"50 Customers\"];\n    Leads -> Qualified;\n    Qualified -> Opportunities;\n    Opportunities -> Customers;\n}"
  },
  "question_visual_type": "graphviz"
}
```

---

## Visual Type Decision Guide

**Ask yourself: "What kind of data am I showing?"**

| Data Type | Visual Type | Example Use Case |
|-----------|-------------|------------------|
| **Numeric data** | `matplotlib` | Show a scatter plot and ask about correlation |
| **Statistical patterns** | `matplotlib` | Show a residual plot and ask about assumptions |
| **Mathematical expressions** | `latex` | Show a formula and ask for interpretation |
| **Process steps** | `mermaid` | Show a workflow and ask about next steps |
| **System architecture** | `graphviz` | Show a component diagram and ask about design |
| **Decision logic** | `mermaid` | Show a decision tree and ask about outcomes |
| **Hierarchies** | `mermaid` or `graphviz` | Show a concept map and ask about relationships |
| **Tabular data** | Include in `question_text` | Show a dataset and ask for calculations |
| **Code** | Include in `question_text` | Show code and ask about behavior |

---

## Implementation in DiagramGenerator

The `DiagramGenerator` class in `cognitive_flashcard_generator/diagram_generator.py` already supports:

1. **Matplotlib** → Renders to base64 PNG image
2. **Plotly** → Returns JSON spec for client-side rendering
3. **Mermaid** → Returns code for client-side rendering
4. **Graphviz** → Renders to SVG
5. **LaTeX** → Handled by frontend (KaTeX/MathJax)

The `QuizGenerator` will process `question_visual` the same way it processes diagrams in explanations.

---

## Backend & Frontend Support

### Backend (`backend/app/models/adaptive_quiz.py`):
The `QuizQuestion` model already supports flexible structures:

```python
class QuizQuestion(BaseModel):
    question_id: str
    question_type: str
    question: Any  # Can be string or dict
    scenario: Optional[Union[str, Dict[str, Any]]]
    # ... other fields
```

The `question_visual` can be included in the `scenario` field or as part of the `question` structure.

### Frontend:
The `DiagramRenderer` component (`frontend/src/components/quiz/DiagramRenderer.jsx`) already renders all diagram types. It can be used for both question visuals and explanation diagrams.

---

## Summary

✅ **All 4 levels** now support `question_visual` and `question_visual_type`
✅ **Generic rules** work for any course type (Data Analytics, ML, Calculus, Software Engineering, etc.)
✅ **Clear guidance** on when to use visuals vs. text-only questions
✅ **Flexible format** supports matplotlib, plotly, mermaid, graphviz, latex
✅ **Backend/frontend** already have infrastructure to render these visuals

---

## Next Steps

When you regenerate quizzes, questions can now include visuals:

```bash
python cognitive_flashcard_generator/learning_materials_cli.py generate-quizzes --course MS5031 --lecture 3
```

**Example output:**
- Questions showing residual plots asking about assumption violations
- Questions showing distributions asking about confidence intervals
- Questions showing formulas asking for interpretation
- Questions showing process flows asking about next steps

All course-agnostic and ready for any subject!

