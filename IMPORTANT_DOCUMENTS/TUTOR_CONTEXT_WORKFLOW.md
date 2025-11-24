# AI Tutor Context Passing Workflow - Complete Explanation

## Overview
This document explains how context is passed through the personalized AI Tutor chat application, from the frontend user input to the final AI response.

---

## ASCII Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                                  │
│                    TutorChatView.jsx                                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                                │
                                │ 1. User types message
                                │    POST /api/tutor/conversations/{id}/stream
                                │    { message: "What is MIS?" }
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MAIN BACKEND (FastAPI - Port 8000)                    │
│                    backend/app/routers/conversations.py                  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ stream_message() endpoint                                         │ │
│  │  • Verifies user authentication                                    │ │
│  │  • Loads conversation from MongoDB                                │ │
│  │  • Extracts: course_id, lecture_id                                │ │
│  │  • Builds session_id: "{user_id}_{course_id}_{lecture_id}"        │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│                          │ 2. Forward to RAG Backend                     │
│                          │    POST {RAG_API}/chat/{course_id}/stream    │
│                          │    { message, session_id }                   │
│                          ▼                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              RAG BACKEND (FastAPI - Port 8001)                           │
│         backend/image_rag_pipeline/app/api/server.py                     │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ stream_chat() endpoint                                             │ │
│  │  • Extracts lecture_id from session_id                             │ │
│  │  • Gets/Creates ConversationManager for course_id + lecture_id     │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│                          │ 3. Call ConversationManager.stream_chat()    │
│                          ▼                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│         ConversationManager (chain.py)                                  │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ STEP 1: Load Memory & History                                      │ │
│  │  • Gets ConversationSummaryBufferMemory for session_id             │ │
│  │  • Loads chat_history (last 6 messages + summary of older)        │ │
│  │  • Filters to HumanMessage + AIMessage only                         │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ STEP 2: Load Foundational Context                                 │ │
│  │  • Reads: courses/{course_id}/slide_analysis/                     │ │
│  │           {lecture_id}_structured_analysis.json                    │ │
│  │  • Extracts: lecture_summary, key_concepts                         │ │
│  │  • Creates "mission statement" for AI:                            │ │
│  │    "=== YOUR ROLE ==="                                             │ │
│  │    "You are an expert AI Tutor..."                                │ │
│  │    "=== THIS LECTURE ==="                                          │ │
│  │    {lecture_summary}                                               │ │
│  │    "=== KEY CONCEPTS ==="                                          │ │
│  │    {key_concepts list}                                             │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│                          │ 4. Invoke Conversational Chain               │
│                          │    chain.invoke({                            │
│                          │      "input": message,                       │
│                          │      "chat_history": chat_history            │
│                          │    })                                         │
│                          ▼                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Conversational Chain (create_conversational_chain)          │
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PHASE 1: Question Contextualization                               │ │
│  │  • If chat_history exists:                                         │ │
│  │    → Reformulate vague questions                                   │ │
│  │    → "Next concept" → "What is another concept from lecture?"       │ │
│  │    → Uses foundational_context + chat_history                       │ │
│  │  • If no history:                                                  │ │
│  │    → Use question as-is                                            │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PHASE 2: Vector Retrieval                                          │ │
│  │  • Embed contextualized question                                   │ │
│  │  • Search Qdrant vector store:                                     │ │
│  │    - Filter by: course_id, lecture_id, type="text"                │ │
│  │    - Top K: 5 most similar chunks                                  │ │
│  │  • Returns: List of Document objects with:                         │ │
│  │    - page_content (text chunk)                                    │ │
│  │    - metadata (context, tags, page_number, etc.)                   │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PHASE 3: Format Retrieved Context                                  │ │
│  │  • Wraps each document:                                           │ │
│  │    <document index="1">                                            │ │
│  │    {page_content}                                                 │ │
│  │    [Topic: {context}]                                              │ │
│  │    [Tags: {tags}]                                                  │ │
│  │    </document>                                                     │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │ PHASE 4: LLM Answer Generation                                     │ │
│  │  • Prompt includes:                                                │ │
│  │    1. Foundational Context (pinned to every response)              │ │
│  │    2. Retrieved documents (formatted)                               │ │
│  │    3. Chat history (for conversation continuity)                    │ │
│  │    4. User's question                                              │ │
│  │  • LLM: Gemini 1.5 Flash                                          │ │
│  │  • Teaching style: Feynman + Walter Lewin                          │ │
│  │  • Streams response chunk by chunk                                 │ │
│  └───────────────────────┬───────────────────────────────────────────┘ │
│                          │                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                │ 5. Stream chunks back
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Response Flow Back                                    │
│                                                                           │
│  • ConversationManager.stream_chat() yields chunks                      │
│  • RAG Backend streams to Main Backend                                  │
│  • Main Backend streams to Frontend                                    │
│  • Frontend updates UI in real-time                                     │
│  • After stream completes:                                              │
│    → Save full response to MongoDB                                      │
│    → Save to ConversationSummaryBufferMemory                            │
│    → Auto-generate conversation title if first message                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Context Components

### 1. **Foundational Context** (PILLAR 1)
**Source**: `courses/{course_id}/slide_analysis/{lecture_id}_structured_analysis.json`

**What it contains**:
- Lecture summary (overview of the lecture)
- Key concepts list (main topics covered)
- Teaching mission statement (how the AI should teach)

**When it's loaded**:
- Once per `ConversationManager` initialization
- Pinned to EVERY AI response (never changes during conversation)

**How it's generated**:
The lecture summary and key concepts are generated during the PDF slide processing pipeline:

1. **Entry Point**: `pdf_slide_processor/main.py`
   - Processes PDF lecture slides
   - Renders slides as images
   - Analyzes each slide with Gemini Vision API

2. **Summary Generation**: `pdf_slide_processor/analyzer.py` → `generate_lecture_summary()`
   - **Input**: All analyzed slide content (titles, main content, key points, math, examples)
   - **Process**:
     - Extracts all text from analyzed slides
     - Combines into a single text document (truncated to ~30,000 chars if needed)
     - Calls Gemini API with a specialized prompt asking for:
       - A concise 3-5 sentence summary
       - 3-7 key concepts
   - **Output**: JSON with `lecture_summary` and `key_concepts` array
   - **LLM Used**: Gemini (same model used for slide analysis)

3. **Saving**: `pdf_slide_processor/extractor.py` → `save_structured_json()`
   - Saves the summary and key concepts along with slide analysis data
   - Output file: `courses/{course_id}/slide_analysis/{lecture_id}_structured_analysis.json`

**Generation Command**:
```bash
python -m pdf_slide_processor.main MS5260 MIS_lec_1-3
```

**Example Prompt Sent to Gemini**:
```
You are an expert academic assistant. You have been given the complete text content 
extracted from a university lecture titled "{lecture_name}" from the course "{course_name}".

Your task is to:
1. Write a concise, one-paragraph summary (3-5 sentences) that captures the main 
   learning objectives and overall theme of this lecture.
2. Identify and list the 3-7 most important, core concepts or topics that a student 
   should understand from this lecture.

LECTURE CONTENT:
{combined_text_from_all_slides}

Please respond in the following JSON format:
{
  "lecture_summary": "A concise paragraph summarizing the main objectives and theme...",
  "key_concepts": [
    "First core concept",
    "Second core concept",
    "Third core concept"
  ]
}
```

**Code Locations**:
- Generation: `pdf_slide_processor/analyzer.py` (lines 452-605)
- Orchestration: `pdf_slide_processor/main.py` (lines 131-140)
- Saving: `pdf_slide_processor/extractor.py` (lines 13-38)

**Example**:
```
=== YOUR ROLE ===
You are an expert AI Tutor helping a student master university-level concepts.
Your teaching style is inspired by Richard Feynman and Walter Lewin...

=== THIS LECTURE ===
This lecture covers Management Information Systems (MIS), their role in 
organizations, and how they provide competitive advantage...

=== KEY CONCEPTS TO COVER ===
1. Management Information Systems (MIS)
2. Information Technology vs Information Systems
3. Sustained Competitive Advantage
4. Resources and Capabilities
...
```

**Code Location**: `backend/image_rag_pipeline/app/utils/lecture_metadata.py`

---

### 2. **Chat History** (PILLAR 2: Hybrid Memory)
**Source**: `ConversationSummaryBufferMemory` (LangChain)

**What it contains**:
- **Recent messages** (last 6): Full text of user and AI messages
- **Older messages**: Automatically summarized to preserve context without token bloat

**Memory Configuration**:
- `max_history_messages`: 6 (keeps last 3 exchanges in full)
- `max_token_limit`: 1500 (triggers summarization when exceeded)

**How it works**:
1. Recent messages stored verbatim for perfect recall
2. When token limit approached, older messages summarized
3. Summary + recent messages = complete context

**Code Location**: `backend/image_rag_pipeline/app/chatbot/chain.py` (ConversationManager class)

---

### 3. **Retrieved Context** (Vector Search)
**Source**: Qdrant Vector Database

**What it contains**:
- Top 5 most semantically similar text chunks from the lecture
- Each chunk includes:
  - Text content (from PDF slides)
  - Metadata (page number, topic, tags, etc.)

**How it works**:
1. User question (or contextualized version) is embedded
2. Vector similarity search in Qdrant
3. Filters by: `course_id`, `lecture_id`, `type="text"`
4. Returns top K most similar chunks

**Code Location**: 
- Retriever: `backend/image_rag_pipeline/app/chatbot/retrievers.py`
- Vector Store: `backend/image_rag_pipeline/app/db/vector_store.py`

---

### 4. **Question Contextualization** (PILLAR 3)
**Purpose**: Reformulate vague follow-up questions into clear, searchable queries

**Examples**:
- "Next concept" → "What is another important concept from this lecture on Information Systems?"
- "Tell me more" → "Provide more details about Sustained Competitive Advantage"
- "What's the difference?" → "What is the difference between IT and IS?"

**How it works**:
- Uses foundational context + chat history to understand intent
- Reformulates only if question is vague
- Clear questions pass through unchanged

**Code Location**: `backend/image_rag_pipeline/app/chatbot/prompts.py` (create_contextualize_question_prompt)

---

## Complete Message Flow Example

### User Input: "What is MIS?"

**Step 1: Frontend** (`TutorChatView.jsx`)
```javascript
// User types message
const userMessage = "What is MIS?";

// Send via streaming API
await streamMessage(conversationId, userMessage, (chunk) => {
  // Update UI with each chunk
  setMessages(prev => [...prev, { content: chunk }]);
});
```

**Step 2: Main Backend** (`conversations.py`)
```python
# Extract conversation info
conversation = await service.get_conversation_with_messages(conversation_id, user_id)
# conversation.course_id = "MS5260"
# conversation.lecture_id = "MIS_lec_1-3"

# Build session_id
session_id = f"{user_id}_{conversation.course_id}_{conversation.lecture_id}"
# Result: "user123_MS5260_MIS_lec_1-3"

# Forward to RAG backend
async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        f"{RAG_API}/chat/{course_id}/stream",
        json={"message": "What is MIS?", "session_id": session_id}
    ) as response:
        async for chunk in response.aiter_bytes():
            yield chunk  # Stream to frontend
```

**Step 3: RAG Backend** (`server.py`)
```python
# Extract lecture_id from session_id
lecture_id = extract_lecture_id_from_session(session_id, course_id)
# Result: "MIS_lec_1-3"

# Get conversation manager (creates if doesn't exist)
manager = get_conversation_manager(course_id, lecture_id)

# Stream response
for chunk in manager.stream_chat(session_id, message):
    yield chunk
```

**Step 4: ConversationManager** (`chain.py`)
```python
# Load memory
memory = get_or_create_memory(session_id)
chat_history = memory.load_memory_variables({}).get("chat_history", [])
# Result: [] (first message, no history)

# Load foundational context (already loaded when manager created)
# This was loaded from: courses/MS5260/slide_analysis/MIS_lec_1-3_structured_analysis.json
foundational_context = """
=== YOUR ROLE ===
You are an expert AI Tutor...
=== THIS LECTURE ===
This lecture covers Management Information Systems...
=== KEY CONCEPTS ===
1. Management Information Systems (MIS)
...
"""

# Invoke chain
response = chain.invoke({
    "input": "What is MIS?",
    "chat_history": []  # Empty for first message
})
```

**Step 5: Conversational Chain** (`chain.py`)
```python
# PHASE 1: Contextualization
# No chat history, so question passes through unchanged
contextualized_question = "What is MIS?"

# PHASE 2: Vector Retrieval
# Embed question
query_embedding = embedder.embed_text("What is MIS?")[0]

# Search vector store
results = vector_store.search(
    course_id="MS5260",
    query_vector=query_embedding,
    filter_type="text",
    lecture_id="MIS_lec_1-3",
    top_k=5
)

# Returns 5 most similar text chunks from the lecture PDF

# PHASE 3: Format Context
formatted_docs = """
<document index="1">
Management Information Systems (MIS) are computer-based systems that provide 
information to support decision-making in organizations...
[Topic: MIS Fundamentals]
[Tags: definition, introduction]
</document>

<document index="2">
MIS combines people, processes, and technology to collect, process, store, 
and distribute information...
[Topic: MIS Components]
[Tags: components, architecture]
</document>
...
"""

# PHASE 4: LLM Generation
# Prompt sent to Gemini:
prompt = f"""
{foundational_context}

Context from course materials:
{formatted_docs}

Student's question: What is MIS?
"""

# LLM generates response using:
# - Foundational context (lecture overview)
# - Retrieved documents (specific content)
# - Teaching philosophy (Feynman + Lewin style)
```

**Step 6: Response Streaming**
```python
# Stream chunks back through the chain
for chunk in chain.stream(...):
    yield chunk  # "Management Information Systems (MIS) are..."
                 # " computer-based systems..."
                 # " that provide information..."
```

**Step 7: Save to Memory**
```python
# After full response received
memory.save_context(
    {"input": "What is MIS?"},
    {"output": "Management Information Systems (MIS) are computer-based systems..."}
)
```

---

## Key Design Decisions

### 1. **Why Three Context Layers?**
- **Foundational Context**: Ensures AI knows the lecture scope (prevents off-topic answers)
- **Chat History**: Maintains conversation continuity (handles follow-ups)
- **Retrieved Context**: Provides specific, accurate information from source material

### 2. **Why Hybrid Memory?**
- Long conversations would exceed token limits
- Summarization preserves important context while saving tokens
- Recent messages in full detail = perfect short-term recall

### 3. **Why Question Contextualization?**
- Vague questions like "Next concept" need context to be searchable
- Vector search works best with clear, specific queries
- Reformulation bridges natural conversation → structured search

### 4. **Why Session-Based Memory?**
- Each user gets separate memory per lecture
- Session ID encodes: `{user_id}_{course_id}_{lecture_id}`
- Allows multiple concurrent conversations without interference

---

## File Reference Map

| Component | File Path |
|-----------|-----------|
| Frontend Chat UI | `frontend/src/views/TutorChatView.jsx` |
| Frontend API Client | `frontend/src/api/tutorApi.js` |
| Main Backend Router | `backend/app/routers/conversations.py` |
| RAG Backend Server | `backend/image_rag_pipeline/app/api/server.py` |
| Conversation Manager | `backend/image_rag_pipeline/app/chatbot/chain.py` |
| Prompts | `backend/image_rag_pipeline/app/chatbot/prompts.py` |
| Foundational Context | `backend/image_rag_pipeline/app/utils/lecture_metadata.py` |
| Vector Retriever | `backend/image_rag_pipeline/app/chatbot/retrievers.py` |
| Vector Store | `backend/image_rag_pipeline/app/db/vector_store.py` |

---

## Summary

The AI Tutor uses a **three-layer context system**:

1. **Foundational Context** (static, lecture-level): Loaded once, pinned to every response
2. **Chat History** (dynamic, conversation-level): Hybrid memory with summarization
3. **Retrieved Context** (dynamic, query-level): Vector search for specific information

This architecture ensures:
- ✅ Accurate answers grounded in source material
- ✅ Conversation continuity across multiple exchanges
- ✅ Efficient token usage for long conversations
- ✅ Context-aware handling of vague follow-up questions

