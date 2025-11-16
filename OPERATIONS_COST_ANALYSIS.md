# Operations Cost Analysis & Batching Strategy

## Overview of 3 Operations

### 1. 📚 CONTENT ENRICHMENT
**Status:** ❌ **NO BATCHING** (Sequential Processing)

**How it works:**
- Processes topics **one at a time** sequentially
- For each topic in a lecture, makes a separate API call
- Example: DAA Lecture 2 has 7 topics → 7 separate API calls

**Token Usage per Topic:**
- **Input:** ~3,000-5,000 tokens (prompt + topic + textbook context)
- **Output:** ~2,000-4,000 tokens (enriched content per topic)
- **Max Output Limit:** 15,000 tokens (recently increased from 8,000)

**Example: DAA Lecture 2 (7 topics)**
- API Calls: 7
- Total Input: ~21,000-35,000 tokens
- Total Output: ~14,000-28,000 tokens

---

### 2. 🎴 FLASHCARD GENERATION
**Status:** ✅ **USES BATCHING** (Content Chunking)

**How it works:**
- Takes enriched content (~60KB for a lecture)
- **Chunks content** into ~25,000 character pieces (overlap: 500 chars)
- Processes each chunk separately
- Example: 60KB content → 3 chunks → 3 API calls

**Token Usage per Chunk:**
- **Input:** ~6,000-8,000 tokens (prompt + 25KB content chunk)
- **Output:** ~4,000-8,000 tokens (5-8 flashcards with diagrams)
- **Max Output Limit:** 30,000 tokens (recently increased from 16,384)

**Example: DAA Lecture 2 (60KB content)**
- Content Chunks: 3
- API Calls: 3
- Total Input: ~18,000-24,000 tokens
- Total Output: ~12,000-24,000 tokens
- **Flashcards Generated:** ~15-20 flashcards

**Batching Strategy:**
- Chunk size: 25,000 characters
- Overlap: 500 characters (for context continuity)
- Prevents hitting input token limits

---

### 3. ❓ QUIZ GENERATION
**Status:** ✅ **USES BATCHING** (Flashcard Batching)

**How it works:**
- Takes all flashcards (e.g., 11 flashcards)
- **Batches flashcards** into groups of 3
- Generates questions for each batch separately
- Combines all questions at the end
- Example: 11 flashcards → 4 batches (3+3+3+2) → 4 API calls per level

**Token Usage per Batch:**
- **Input:** ~1,500-2,500 tokens (prompt + 3 flashcards JSON)
- **Output:** ~3,000-6,000 tokens (15 questions: 5 per flashcard × 3)
- **Max Output Limit:** 30,000 tokens (recently increased from 16,384)

**Example: DAA Lecture 2 (11 flashcards, 4 levels)**
- Flashcard Batches: 4 batches
- API Calls per Level: 4
- Total API Calls (4 levels): 16
- Total Input: ~24,000-40,000 tokens
- Total Output: ~48,000-96,000 tokens
- **Questions Generated:** ~220 questions (55 per level × 4 levels)

**Batching Strategy:**
- Batch size: 3 flashcards per batch
- Questions per batch: ~15 questions (5 per flashcard)
- Prevents hitting output token limits (was causing truncation)

---

## 💰 COST ANALYSIS

### Pricing Assumptions (Gemini 2.5 Flash)
- **Input Tokens:** $0.075 per 1M tokens ($0.000075 per 1K tokens)
- **Output Tokens:** $0.30 per 1M tokens ($0.0003 per 1K tokens)

### Cost Per Operation

#### 1. Content Enrichment (NO BATCHING)
**Per Lecture (7 topics):**
- Input: 35,000 tokens × $0.000075 = **$2.625**
- Output: 28,000 tokens × $0.0003 = **$8.40**
- **Total: $11.025 per lecture**

**If we batched topics (hypothetical):**
- Could combine 2-3 topics per call
- API Calls: 3 instead of 7
- Input: ~25,000 tokens × $0.000075 = **$1.875**
- Output: ~20,000 tokens × $0.0003 = **$6.00**
- **Total: $7.875 per lecture**
- **Savings: $3.15 per lecture (28.6% reduction)**

---

#### 2. Flashcard Generation (WITH BATCHING)
**Per Lecture (3 chunks):**
- Input: 24,000 tokens × $0.000075 = **$1.80**
- Output: 24,000 tokens × $0.0003 = **$7.20**
- **Total: $9.00 per lecture**

**If we didn't batch (hypothetical - single call):**
- Would need to send entire 60KB content
- Input: ~15,000 tokens × $0.000075 = **$1.125**
- Output: Would hit token limit and truncate → **FAILURE**
- **Result: Incomplete flashcards, wasted cost**

**Batching Benefit:** Prevents failures, ensures complete output

---

#### 3. Quiz Generation (WITH BATCHING)
**Per Lecture (11 flashcards, 4 levels, 4 batches per level):**
- Total API Calls: 16 (4 batches × 4 levels)
- Input: 40,000 tokens × $0.000075 = **$3.00**
- Output: 96,000 tokens × $0.0003 = **$28.80**
- **Total: $31.80 per lecture**

**If we didn't batch (hypothetical - single call per level):**
- Would send all 11 flashcards at once
- Input: ~4,000 tokens × $0.000075 = **$0.30** (4 levels = $1.20)
- Output: Would hit 30K token limit, truncate at ~36 questions
- **Result: Only 36/55 questions generated (65% loss)**
- Output: 36,000 tokens × $0.0003 = **$10.80** (4 levels = $43.20)
- **Total: $44.40 per lecture**
- **But: Incomplete quizzes, poor quality**

**Batching Benefit:** 
- **Cost:** $31.80 vs $44.40 = **$12.60 savings (28.4% reduction)**
- **Quality:** 100% questions generated vs 65%
- **Reliability:** No JSON truncation errors

---

## 📊 SUMMARY TABLE

| Operation | Batching? | API Calls | Input Tokens | Output Tokens | Cost | Savings from Batching |
|-----------|-----------|-----------|--------------|---------------|------|----------------------|
| **Content Enrichment** | ❌ No | 7 | 35,000 | 28,000 | **$11.03** | **$3.15** (28.6%) |
| **Flashcard Generation** | ✅ Yes | 3 | 24,000 | 24,000 | **$9.00** | Prevents failures |
| **Quiz Generation** | ✅ Yes | 16 | 40,000 | 96,000 | **$31.80** | **$12.60** (28.4%) |

**Total Cost per Lecture:** $51.83

---

## 💡 POTENTIAL OPTIMIZATIONS

### 1. Content Enrichment Batching (Not Currently Implemented)
**Current:** 7 topics = 7 API calls
**Optimized:** Batch 2-3 topics per call = 3 API calls
**Savings:** $3.15 per lecture (28.6% reduction)

**Why not implemented?**
- Topics are independent and benefit from focused generation
- Risk of lower quality if topics are too different
- Current approach ensures high-quality, topic-specific content

### 2. Quiz Generation Batch Size Optimization
**Current:** 3 flashcards per batch
**Could try:** 4 flashcards per batch
**Trade-off:** 
- Fewer API calls (12 instead of 16)
- Higher risk of hitting token limits
- Current size (3) is optimal balance

---

## 🎯 KEY INSIGHTS

1. **Batching is Critical for Quality:**
   - Without batching, quiz generation loses 35% of questions
   - Flashcard generation would fail completely on large content

2. **Content Enrichment is the Costliest:**
   - $11.03 per lecture (21% of total cost)
   - Could benefit from batching, but quality trade-off exists

3. **Quiz Generation is Most Expensive:**
   - $31.80 per lecture (61% of total cost)
   - But batching ensures 100% completion vs 65% without it

4. **Total Cost per Lecture:** ~$52
   - For a course with 7 lectures: ~$364
   - For 10 courses: ~$3,640

---

## 📈 SCALING IMPLICATIONS

**For 100 Lectures:**
- Current Cost: ~$5,183
- With Content Enrichment Batching: ~$4,868
- **Potential Savings: $315 (6.1%)**

**For 1,000 Lectures:**
- Current Cost: ~$51,830
- With Content Enrichment Batching: ~$48,680
- **Potential Savings: $3,150 (6.1%)**

---

*Last Updated: Based on current implementation with 30K token limits for flashcards/quizzes and 15K for enrichment*

