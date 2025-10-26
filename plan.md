# Aggressive Mathematical Visualizations Strategy

## Overview

Enhance the flashcard generation system to prioritize mathematical visualizations using Graphviz DOT code. The AI will be strongly encouraged to generate technical diagrams for mathematical concepts while maintaining our proven high-volume flashcard output.

## Foundation (Already in Place)

These critical optimizations MUST remain unchanged:
- ✅ `max_output_tokens`: 16384 (doubled capacity)
- ✅ `max_chunk_size`: 10000 (smaller chunks for reliability)
- ✅ Prompt target: "3-7 flashcards" per chunk

## The New Approach: Emphatic Generation

### Key Principle

**Shift from "Optional" to "Expected"**: For mathematical/statistical/algorithmic concepts, the AI should actively strive to generate Graphviz visualizations, with pragmatic exceptions only for purely qualitative answer types (like analogies or ELI5 when they're non-technical).

### What Changes

**File:** `prompts/intelligent_flashcard_prompt.txt`

The Graphviz section (lines 178-236) will be completely rewritten with these changes:

#### 1. Reframe the Core Directive (Lines 178-182)

**Current (too cautious):**
```
IMPORTANT: This is OPTIONAL and CONDITIONAL. Only generate Graphviz DOT code when it genuinely adds mathematical depth.
```

**New (emphatic):**
```
GUIDELINE: For mathematical, statistical, or algorithmic concepts, you are EXPECTED to generate Graphviz visualizations. Prioritize the `concise` and `example` answer types at minimum. While you may leave qualitative answer types (like `analogy` or `eli5`) empty if they're purely textual, you should strive to provide at least 1-2 high-quality mathematical visualizations per flashcard when the topic is quantitative.
```

#### 2. Add "No Excuses" Clause (New section after line 182)

**New addition:**
```
IMPORTANT: Do not leave all `math_visualizations` fields empty if the flashcard topic is mathematical. If a full diagram is too complex, simplify it:
- Visualize just the core formula or equation
- Show a single step of an algorithm
- Create a simplified coordinate plot
- Display a basic distribution curve

An empty string is acceptable for individual answer types (especially `analogy` and `eli5` if they're purely qualitative), but not for the entire `math_visualizations` object when dealing with quantitative concepts.
```

#### 3. Expand "When to Generate" Examples (Lines 184-189)

**Add to the existing list:**
```
- Decision boundaries in classification problems
- Cost function optimization (e.g., gradient descent paths)
- Matrix operations and transformations
- Simple data distributions (histograms, scatter plots with trend lines)
- Probability distributions (Normal, Binomial, etc.)
```

#### 4. Add Second Example: Formula Visualization (After line 228)

**New example to add:**
```
**EXAMPLE 2 (Visualizing R-squared Formula):**
```
/* layout=dot */
digraph R_squared {
  rankdir=LR;
  node [shape=plaintext, fontsize=14];
  
  R2 [label="R²"];
  equals [label="=", shape=none];
  
  subgraph cluster_formula {
    label="";
    style=invisible;
    
    numerator [label="SSR\n(Sum of Squares Regression)"];
    divider [label="―――――――――――――――", shape=none, fontsize=20];
    denominator [label="SST\n(Total Sum of Squares)"];
    
    numerator -> divider [style=invis];
    divider -> denominator [style=invis];
  }
  
  R2 -> equals [style=invis];
  equals -> numerator [style=invis];
}
```

This shows how to visualize mathematical formulas using simple node arrangements.
```

#### 5. Update Quality Guidelines (Lines 230-235)

**Replace with:**
```
**QUALITY GUIDELINES:**
1. **Prioritize generation**: For mathematical concepts, aim to fill at least `concise` and `example` fields
2. **Simplify when needed**: A simple, clear diagram beats a complex, confusing one
3. **Use descriptive labels**: Make node labels self-explanatory
4. **Include layout engine**: Always specify the layout engine in a comment (e.g., `/* layout=dot */`)
5. **Valid syntax**: Ensure DOT code is syntactically correct
6. **Be pragmatic**: It's acceptable to leave `analogy` or `eli5` empty if they're purely qualitative, but don't skip technical answer types
```

#### 6. Update Final Instructions (Line 383)

**Change from:**
```
The `math_visualizations` object must contain ALL 6 keys: `concise`, `analogy`, `eli5`, `real_world_use_case`, `common_mistakes`, `example` (use empty string "" when mathematical visualization is not applicable - this is OPTIONAL and CONDITIONAL)
```

**To:**
```
The `math_visualizations` object must contain ALL 6 keys: `concise`, `analogy`, `eli5`, `real_world_use_case`, `common_mistakes`, `example`. For mathematical concepts, strive to provide at least 1-2 visualizations (prioritize `concise` and `example`). Use empty string "" for qualitative answer types or when a diagram truly doesn't add value.
```

## Expected Outcomes

With these changes, we expect:
- **70-80% of mathematical flashcards** will have at least one Graphviz visualization (up from 0%)
- **30-40% of mathematical flashcards** will have 2+ visualizations
- **Maintained flashcard count**: 7+ flashcards per lecture (our optimizations protect this)
- **Higher educational value**: Students get precise mathematical diagrams alongside conceptual Mermaid diagrams

## Why This Works

1. **Clear Expectations**: The AI knows mathematical visualizations are a priority, not optional
2. **Pragmatic Flexibility**: We still allow empty strings for truly qualitative content
3. **Multiple Examples**: Two diverse examples (coordinate plot + formula) show the range of possibilities
4. **Protected Volume**: Our token limit and chunking strategy ensure flashcard count remains high even with more complex generation

## Implementation

**Single file change:** `prompts/intelligent_flashcard_prompt.txt`

All backend rendering and frontend display code is already in place and working correctly (as evidenced by the proper JSON structure in the generated files).

## Testing Plan

After implementing the prompt changes:
1. Delete existing `DAA_lec_4` flashcards
2. Regenerate with: `python -m cognitive_flashcard_generator.main MS5031`
3. Verify:
   - Flashcard count remains 7+ per lecture
   - `math_visualizations` fields are populated for mathematical concepts
   - Generated DOT code is syntactically valid
   - Rendered images appear correctly in the frontend

