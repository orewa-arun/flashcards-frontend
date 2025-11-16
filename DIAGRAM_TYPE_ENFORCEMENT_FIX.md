# DIAGRAM TYPE ENFORCEMENT FIX

## Problem Identified

The AI was generating **Mermaid diagrams for statistical data visualization**, which is fundamentally wrong for a Data Analytics course.

### Example of the Issue

**Bad Output (what was happening):**
```json
{
  "diagram": {
    "type": "mermaid",
    "chart": "graph TD;\n    A[Fitted Values (X-axis)] --> B[Residuals (Y-axis)];\n    B --> C{Spread of Residuals?};\n    C -- Increases with X --> D[Funnel Shape];\n    D --> E[Heteroscedasticity];"
  },
  "diagram_type": "mermaid"
}
```

**Why This is Terrible:**
- Students need to **SEE actual residual plots** (scatter plots with data points), not text boxes and arrows describing them
- Richard Feynman and 3Blue1Brown would NEVER use a flowchart to teach residual patterns
- This provides zero visual intuition about what heteroscedasticity actually looks like in data

**What Students Actually Need:**
```json
{
  "diagram": {
    "type": "matplotlib",
    "plot_type": "scatter",
    "params": {
      "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
      "y": [0.5, 0.8, 1.2, 1.8, 2.5, 3.2, 4.0, 4.8, 5.5, 6.2],
      "title": "Example of Heteroscedasticity (Residual Plot)",
      "xlabel": "Fitted Values",
      "ylabel": "Residuals"
    }
  },
  "diagram_type": "matplotlib"
}
```
- Actual scatter plot showing residuals **fanning out** as fitted values increase
- Visual pattern recognition is the learning objective
- This is what textbooks and data visualization experts use

---

## Root Cause

The prompts were **too weak** in distinguishing between:
1. **Statistical data visualization** → ALWAYS Matplotlib
2. **Conceptual process flows** → Mermaid/Graphviz OK

The AI was confused and thought "diagram = Mermaid is fine" for everything.

---

## Solution Applied

### Updated All 4 Quiz Prompt Levels with Critical Rule

Added **explicit, non-negotiable instructions** at the top of the "Visual Type Decision Tree" section:

```
### Visual Type Decision Tree (Enhanced for Data Analytics)

🚨 CRITICAL RULE: STATISTICAL DATA = MATPLOTLIB, NOT MERMAID 🚨

**NEVER use Mermaid for:**
- ❌ Residuals (use matplotlib scatter plot)
- ❌ Distributions (use matplotlib probability curves)
- ❌ Scatter plots (use matplotlib)
- ❌ Regression lines (use matplotlib)
- ❌ Confidence intervals on plots (use matplotlib with shaded regions)
- ❌ Hypothesis test visualizations (use matplotlib with distributions)
- ❌ Any actual data visualization (use matplotlib)

**Mermaid is ONLY for:**
- ✅ Process flows (e.g., "Steps to check assumptions")
- ✅ Concept hierarchies (e.g., "Types of variables")
- ✅ Decision trees (e.g., "Which test to use when?")
```

### Added Strong Justifications

For each visual type, added **"Why"** sections to reinforce the reasoning:

**Statistical Inference (ALWAYS Matplotlib):**
- **Example:** Distribution with shaded 95% CI, marked critical values showing real probability regions
- **Why:** Students need to SEE the shaded regions, not read text boxes about them

**Regression Analysis (ALWAYS Matplotlib):**
- **Example:** Scatter with fitted line showing R², residual plot showing heteroscedasticity pattern
- **Why:** Students need to SEE residual patterns (fanning, curves), not flowcharts describing them

---

## Files Updated

✅ `prompts/level_1_quiz_prompt.txt`
✅ `prompts/level_2_quiz_prompt.txt`
✅ `prompts/level_3_quiz_prompt.txt`
✅ `prompts/level_4_quiz_prompt.txt`

---

## Impact

### Before Fix:
- AI generates Mermaid for residuals, distributions, scatter plots
- Students get flowcharts instead of actual data visualizations
- Zero visual pattern recognition learning
- Fundamentally undermines the Data Analytics course goals

### After Fix:
- AI MUST use Matplotlib for all statistical data
- Students see actual scatter plots, distributions, residual patterns
- Visual pattern recognition aligned with textbook standards
- Mermaid reserved for process flows only (e.g., "Steps in hypothesis testing")

---

## Next Steps

**To get properly fixed quizzes, regenerate them:**

```bash
source .venv/bin/activate

# Regenerate all levels for a lecture
python cognitive_flashcard_generator/learning_materials_cli.py generate-quizzes --course MS5031 --lecture 3

# Or regenerate all lectures
for lec in 1 2 3 5 6 7; do
  python cognitive_flashcard_generator/learning_materials_cli.py generate-quizzes --course MS5031 --lecture $lec
done
```

**The AI will now:**
1. Generate Matplotlib plots for residuals, distributions, scatter plots
2. Reserve Mermaid ONLY for process flows and concept hierarchies
3. Align with Feynman/3Blue1Brown teaching philosophy (show, don't tell)

---

## Validation

After regeneration, check a quiz file and verify:

**✅ Good (Matplotlib for data):**
```json
{
  "diagram": {
    "type": "matplotlib",
    "plot_type": "scatter",
    "params": {...}
  },
  "diagram_type": "matplotlib"
}
```

**❌ Bad (Mermaid for data):**
```json
{
  "diagram": {
    "type": "mermaid",
    "chart": "graph TD; A[Residuals] --> B[Fanning];"
  },
  "diagram_type": "mermaid"
}
```

If you see the bad pattern after regeneration, the prompts failed. Report immediately.

---

## Philosophy

**Richard Feynman's Teaching Principle:**
> "If you can't explain it with a simple diagram showing the actual phenomenon, you don't understand it."

**3Blue1Brown's Visualization Standard:**
> "Animate the math. Show the pattern. Make it visual. Don't describe it—draw it."

**Our Standard:**
> Statistical data = Matplotlib. Process flows = Mermaid. No exceptions.

