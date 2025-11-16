# CURRENT EXPLANATION CRITERIA

## Overview

All quiz levels (1-4) now use **Enhanced Explanations** with step-by-step breakdowns, diagrams, LaTeX, and business context. The structure is consistent across levels, with increasing depth and complexity.

---

## Level 1: Basic Understanding

### Section 11: Enhanced Explanations - WORLD-CLASS STANDARD

**CRITICAL: ALL questions MUST have enhanced explanations. For Level 1, use step-by-step when helpful for understanding.**

### When to Include Step-by-Step:
- **ALWAYS** for questions involving formulas or calculations
- **WHEN HELPFUL** for conceptual questions (use Feynman Test from Section 6)
- **OPTIONAL** for simple definition questions (can use just `text` field)

### Explanation Structure:
```json
"explanation": {
  "text": "Brief 2-3 sentence summary",
  "step_by_step": [
    {
      "step": 1,
      "title": "Step title (if helpful)",
      "content": "Detailed explanation",
      "latex": "\\text{LaTeX if applicable}",
      "diagram": {"type": "matplotlib", "plot_type": "normal_distribution", "params": {...}},
      "diagram_type": "matplotlib"
    }
  ],
  "interpretation": "What this means (optional)",
  "business_context": "Real-world application (optional)"
}
```

**Note:** For Level 1, you can use a simpler format with just `text` if step-by-step doesn't add value, but diagrams should still be included when they help understanding.

---

## Level 2: Application

### Section 11: Enhanced Explanations - WORLD-CLASS STANDARD

**CRITICAL: ALL questions MUST have enhanced explanations with step-by-step breakdowns when helpful.**

### When to Include Step-by-Step:
- **ALWAYS** for questions involving calculations, formulas, or multi-step reasoning
- **ALWAYS** for statistical concepts
- **WHEN HELPFUL** for conceptual questions (use Feynman Test from Section 6)

### Explanation Structure:
```json
"explanation": {
  "text": "Brief 2-3 sentence summary",
  "step_by_step": [
    {
      "step": 1,
      "title": "Step title",
      "content": "Detailed explanation",
      "latex": "\\text{LaTeX if applicable}",
      "diagram": {"type": "matplotlib", "plot_type": "scatter_regression", "params": {...}},
      "diagram_type": "matplotlib"
    }
  ],
  "interpretation": "What this means",
  "business_context": "Real-world application"
}
```

---

## Level 3: Analysis

### Section 11: Enhanced Explanations - WORLD-CLASS STANDARD

**CRITICAL: ALL questions MUST have enhanced explanations with step-by-step breakdowns and diagrams.**

### When to Include Diagrams:
- **ALWAYS** for statistical concepts (distributions, confidence intervals, regression)
- **ALWAYS** for multi-step calculations or formulas
- **WHEN HELPFUL** for conceptual relationships (use Feynman Test from Section 6)

### Explanation Structure:
```json
"explanation": {
  "text": "Brief 2-3 sentence summary identifying the trick/misconception",
  "step_by_step": [
    {
      "step": 1,
      "title": "Step title (e.g., 'Identify the assumption violation')",
      "content": "Detailed explanation of this step",
      "latex": "\\text{LaTeX formula if applicable}",
      "diagram": {
        "type": "matplotlib",
        "plot_type": "normal_distribution",
        "params": {
          "mean": 2.5,
          "std": 0.4,
          "title": "Distribution showing the concept"
        }
      },
      "diagram_type": "matplotlib"
    }
  ],
  "interpretation": "What this result means in plain language",
  "business_context": "Real-world business application or implication"
}
```

---

## Level 4: Synthesis

### Section 11: Enhanced Explanations - WORLD-CLASS STANDARD

**CRITICAL: ALL Level 4 questions MUST have comprehensive enhanced explanations with detailed step-by-step breakdowns.**

### When to Include Step-by-Step:
- **ALWAYS** for Level 4 questions (synthesis requires detailed reasoning)
- **ALWAYS** show the multi-step synthesis process
- **ALWAYS** include diagrams for complex statistical concepts

### Explanation Structure:
```json
"explanation": {
  "text": "Brief summary of the synthesis required",
  "step_by_step": [
    {
      "step": 1,
      "title": "Analyze first-order effects",
      "content": "Detailed analysis...",
      "latex": "\\text{Complex formula}",
      "diagram": {"type": "matplotlib", "plot_type": "...", "params": {...}},
      "diagram_type": "matplotlib"
    },
    {
      "step": 2,
      "title": "Identify second-order effects",
      "content": "Cascading implications...",
      "diagram": {"type": "graphviz", "code": "digraph {...}"},
      "diagram_type": "graphviz"
    }
  ],
  "interpretation": "What this synthesis reveals",
  "business_context": "Strategic business implications"
}
```

---

## Common Structure Across All Levels

### Required Fields:

1. **`text`** (string, required)
   - Brief 2-3 sentence summary
   - Level 3: Identifies the trick/misconception
   - Level 4: Summarizes the synthesis required

2. **`step_by_step`** (array, required for Level 2-4, optional for Level 1)
   - Array of step objects
   - Each step contains:
     - `step` (int): Step number
     - `title` (string): Step title
     - `content` (string): Detailed explanation
     - `latex` (string, optional): LaTeX formula if applicable
     - `diagram` (object/string, optional): Diagram specification
     - `diagram_type` (string, optional): Type of diagram (matplotlib, plotly, mermaid, graphviz, svg)

3. **`interpretation`** (string, optional)
   - What this result means in plain language
   - Business implications

4. **`business_context`** (string, optional)
   - Real-world business application or implication
   - Strategic implications for Level 4

---

## Diagram Type Rules (Applied to All Levels)

### 🚨 CRITICAL RULE: STATISTICAL DATA = MATPLOTLIB, NOT MERMAID 🚨

**NEVER use Mermaid for:**
- ❌ Residuals (use matplotlib scatter plot)
- ❌ Distributions (use matplotlib probability curves)
- ❌ Scatter plots (use matplotlib)
- ❌ Regression lines (use matplotlib)
- ❌ Confidence intervals on plots (use matplotlib with shaded regions)
- ❌ Hypothesis test visualizations (use matplotlib with distributions)
- ❌ Any actual data visualization (use matplotlib)

**Mermaid/Graphviz is ONLY for:**
- ✅ Process flows (e.g., "Steps to check assumptions")
- ✅ Concept hierarchies (e.g., "Types of variables")
- ✅ Decision trees (e.g., "Which test to use when?")

---

## Validation Checklist (All Levels)

From the Final Validation Checklist sections:

- **Explanation:** Does it follow the Level X template? Does it explain *why*?
- **Level 3:** Does it *expose the trick*?
- **Level 4:** Does it explain the *synthesis*?

---

## Summary

| Level | Step-by-Step | Diagrams | Complexity |
|-------|--------------|----------|------------|
| **Level 1** | Optional (when helpful) | When helpful | Simple |
| **Level 2** | Always (when helpful) | Always for stats | Moderate |
| **Level 3** | Always | Always for stats | Complex |
| **Level 4** | Always (comprehensive) | Always for stats | Very Complex |

**All levels support:**
- ✅ Enhanced explanation structure with `text`, `step_by_step`, `interpretation`, `business_context`
- ✅ LaTeX formulas in steps
- ✅ Diagrams (Matplotlib for data, Mermaid/Graphviz for processes)
- ✅ Business context and real-world applications

