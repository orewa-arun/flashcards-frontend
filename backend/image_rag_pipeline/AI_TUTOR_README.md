# AI Tutor - World-Class Conversational Memory System

## Overview

The AI Tutor is a conversational RAG (Retrieval-Augmented Generation) chatbot designed to help students master university-level course material. It features a **three-pillar architecture** that ensures robust, context-aware conversations with perfect memory retention—mirroring the experience of chatting with ChatGPT.

### Key Features

- **Foundational Context Pinning**: Every conversation is anchored to the lecture's main topics and learning objectives
- **Hybrid Memory System**: Maintains perfect recall of recent exchanges while summarizing older context
- **Intelligent Question Reformulation**: Understands vague follow-ups like "Next concept.." and transforms them into precise search queries
- **Teaching Excellence**: Inspired by Richard Feynman and Walter Lewin's teaching philosophies
- **Multi-Lecture Support**: Each lecture gets its own foundational context and memory space

---

## Architecture: The Three Pillars

### Pillar 1: Foundational Context Pinning (The "Mission Statement")

**Problem Solved**: Context amnesia—the bot forgetting the overall goal of the conversation.

**How It Works**:
1. When a lecture PDF is processed, the system generates a comprehensive summary and extracts 3-7 key concepts
2. This metadata is saved in `courses/{course_id}/slide_analysis/{lecture_id}_structured_analysis.json`
3. When a chat session starts, this summary is loaded and formatted into a "Foundational Context"
4. This context is **pinned** to every LLM call—it never gets summarized away or forgotten

**Example Foundational Context**:
```
=== YOUR ROLE ===
You are an expert AI Tutor helping a student master university-level concepts.
Your teaching style is inspired by Richard Feynman and Walter Lewin...

=== THIS LECTURE ===
This lecture introduces the concept of sustained competitive advantage through
the strategic use of Information Systems (IS)...

=== KEY CONCEPTS TO COVER ===
1. Sustained Competitive Advantage
2. IS and Organization Relationship
3. IT vs. IS

=== YOUR TASK ===
Help the student understand these concepts deeply, one at a time.
When they ask vague questions like 'next concept', use the key concepts list above...
```

**Impact**: The AI always knows what lecture it's teaching and what topics to cover. No more generic, off-topic responses.

---

### Pillar 2: Hybrid Memory (Short-Term Sharpness, Long-Term Wisdom)

**Problem Solved**: Loss of recent conversational context in long discussions.

**How It Works**:
- Uses LangChain's `ConversationSummaryBufferMemory`
- **Short-Term**: Keeps the last **6 messages** (3 exchanges) in full, verbatim detail
- **Long-Term**: Older messages are progressively summarized to preserve key information
- **Token Budget**: 1500 tokens before summarization kicks in

**Benefits**:
- Perfect recall for immediate follow-ups ("What did you mean by that?")
- Efficient, summarized memory for the entire conversation flow
- No context overflow or hallucination in long sessions

**Code Location**: `backend/image_rag_pipeline/app/chatbot/chain.py` → `ConversationManager.__init__()`

---

### Pillar 3: Context-Aware Question Reformulation

**Problem Solved**: Brittle handling of vague follow-up questions.

**How It Works**:
1. The user asks a vague question like "Next concept.." or "Tell me more"
2. The reformulation step receives:
   - The **Foundational Context** (from Pillar 1)
   - The **Recent Chat History** (from Pillar 2)
   - The **Vague User Input**
3. A specialized LLM prompt uses **few-shot learning** to transform the vague input into a standalone, searchable query
4. Example transformation:
   - Input: "Next concept.."
   - Output: "Explain the relationship between Information Systems and Organizations, which is the next key concept after Sustained Competitive Advantage."

**Code Location**: 
- Prompt: `backend/image_rag_pipeline/app/chatbot/prompts.py` → `CONTEXTUALIZE_QUESTION_SYSTEM_PROMPT`
- Chain: `backend/image_rag_pipeline/app/chatbot/chain.py` → `contextualize_with_logging()`

---

## System Flow

```
1. User sends message
       ↓
2. Extract lecture_id from session_id
       ↓
3. Load Foundational Context (Pillar 1)
       ↓
4. Get or create ConversationManager with Hybrid Memory (Pillar 2)
       ↓
5. Load recent chat history
       ↓
6. Reformulate question if needed (Pillar 3)
       ↓
7. Retrieve relevant documents from vector store
       ↓
8. Generate answer with LLM (with Foundational Context pinned)
       ↓
9. Save interaction to memory
       ↓
10. Return response
```

---

## File Structure

```
backend/image_rag_pipeline/
├── app/
│   ├── api/
│   │   └── server.py                  # FastAPI endpoints + session parsing
│   ├── chatbot/
│   │   ├── chain.py                   # ConversationManager + 3-pillar chain
│   │   ├── prompts.py                 # Foundational context + reformulation prompts
│   │   └── retrievers.py              # LangChain retriever wrapper
│   ├── db/
│   │   └── vector_store.py            # Qdrant vector database
│   ├── ingestion/
│   │   ├── loader.py                  # PDF/JSON hybrid ingestion
│   │   └── embedder.py                # Text embedding
│   ├── retrieval/
│   │   └── query.py                   # Vector search
│   └── utils/
│       ├── config.py                  # Configuration
│       └── lecture_metadata.py        # 🆕 Load summaries + create foundational context
│
├── AI_TUTOR_README.md                 # This file
└── requirements.txt                   # Python dependencies

courses/
└── {course_id}/
    └── slide_analysis/
        └── {lecture_id}_structured_analysis.json  # 🆕 Contains lecture_summary + key_concepts

pdf_slide_processor/
├── analyzer.py                        # 🆕 generate_lecture_summary() method
├── extractor.py                       # 🆕 Updated to save metadata
└── main.py                            # 🆕 Calls summary generation
```

---

## Setup & Usage

### 1. Install Dependencies

```bash
cd backend/image_rag_pipeline
source ../../.venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `.env` in the project root:

```bash
# Google AI (Gemini) API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# LLM Configuration
LLM_MODEL=gemini-1.5-flash-001
LLM_TEMPERATURE=0.5

# Chat Configuration
CHAT_TOP_K=5
CHAT_MAX_HISTORY=6           # Keep last 6 messages verbatim (PILLAR 2)
CHAT_TOKEN_LIMIT=1500        # Token limit before summarization (PILLAR 2)

# Vector Database
QDRANT_PATH=./backend/image_rag_pipeline/data/qdrant_storage
```

### 3. Process a New Lecture (Generate Summary + Key Concepts)

When you add a new lecture PDF, run the analyzer to generate its foundational context:

```bash
cd /path/to/project
source .venv/bin/activate
python -m pdf_slide_processor.main MS5260 MIS_lec_1-3
```

This will:
1. Extract slides as images
2. Analyze slide content with Gemini Vision
3. **🆕 Generate lecture summary and key concepts**
4. Save everything to `courses/MS5260/slide_analysis/MIS_lec_1-3_structured_analysis.json`

The JSON will now include:
```json
{
  "lecture_summary": "This lecture introduces...",
  "key_concepts": ["Concept 1", "Concept 2", ...],
  "total_slides": 23,
  "slides": [...]
}
```

### 4. Ingest into Vector Store

```bash
cd backend/image_rag_pipeline
python -m scripts.batch_ingest MS5260
```

### 5. Start the RAG API Server

```bash
cd backend/image_rag_pipeline
python -m app.api.server
```

The server will start on `http://localhost:8001`.

### 6. Test the Chat

**Using the Frontend**:
1. Navigate to a lecture page (e.g., `/courses/MS5260/MIS_lec_1-3`)
2. Click "Personalised AI Tutor"
3. Start chatting!

**Using cURL**:
```bash
curl -X POST "http://localhost:8001/chat/MS5260" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the main concepts from this lecture?",
    "session_id": "test_user_MS5260_MIS_lec_1-3"
  }'
```

---

## Debugging & Logging

The system includes **enhanced logging** to trace the entire conversational flow:

### Server Logs

When you send a message, you'll see:

```
=================================================================
💬 NEW MESSAGE | Session: user123_MS5260_MIS_lec_1-3
   User said: 'Next concept..'
=================================================================
📚 MEMORY | Loaded 4 messages, filtered to 4 (Human/AI only)
📜 RECENT HISTORY (last 4 messages):
   👤 User: Can you explain the main concepts from this lecture?
   🤖 Assistant: The lecture covers Management Information Systems, Sustained...
   👤 User: Tell me about the first one
   🤖 Assistant: Sustained Competitive Advantage is when a company...

🔄 REFORMULATION STEP
   Original question: 'Next concept..'
   Chat history length: 4 messages
   ✅ Reformulated to: 'What is the relationship between Information Systems and Organizations, the next key concept after Sustained Competitive Advantage?'
   Reason: Vague follow-up detected, made standalone for vector search

🚀 INVOKING CHAIN...
✅ RESPONSE GENERATED
   Length: 850 characters
   Preview: The relationship between Information Systems (IS) and Organizations...
💾 Interaction saved to memory
=================================================================
```

### Key Log Markers

- `💬 NEW MESSAGE`: A new user message arrived
- `📚 MEMORY`: Chat history loaded from memory
- `📜 RECENT HISTORY`: Last 4 messages being used for context
- `🔄 REFORMULATION STEP`: Question contextualization in progress
- `✅ Reformulated to`: The improved, standalone question for vector search
- `🚀 INVOKING CHAIN`: Calling the full RAG pipeline
- `💾 Interaction saved`: Memory updated

---

## How the Three Pillars Work Together

### Example Conversation Flow

**User**: "Can you explain the main concepts from this lecture? in a table.."

**System**:
1. **Pillar 1**: Loads foundational context → Knows this is the MIS lecture with 3 key concepts
2. **Pillar 2**: No prior history, starts fresh memory
3. **Pillar 3**: Question is clear, no reformulation needed
4. Retrieves relevant docs from vector store
5. Generates a table with all 3 concepts

**User**: "Next concept.."

**System**:
1. **Pillar 2**: Loads recent history → Sees you just discussed "Sustained Competitive Advantage"
2. **Pillar 3**: Reformulates "Next concept.." →"What is the relationship between Information Systems and Organizations?"
3. **Pillar 1**: Knows this is concept #2 from the foundational context
4. Retrieves docs about IS/Organization relationship
5. Generates detailed explanation

---

## Configuration Parameters

| Parameter | Default | Description | Pillar |
|-----------|---------|-------------|--------|
| `LLM_MODEL` | `gemini-1.5-flash-001` | Gemini model for chat | All |
| `LLM_TEMPERATURE` | `0.5` | Creativity vs. determinism | All |
| `CHAT_TOP_K` | `5` | Number of docs to retrieve | - |
| `CHAT_MAX_HISTORY` | `6` | Messages to keep verbatim | Pillar 2 |
| `CHAT_TOKEN_LIMIT` | `1500` | Tokens before summarization | Pillar 2 |

---

## API Endpoints

### POST `/chat/{course_id}`

Send a message to the AI tutor.

**Request**:
```json
{
  "message": "What is MIS?",
  "session_id": "user123_MS5260_MIS_lec_1-3"
}
```

**Response**:
```json
{
  "answer": "Management Information Systems (MIS) refers to...",
  "session_id": "user123_MS5260_MIS_lec_1-3"
}
```

**Session ID Format**: `{user_uid}_{course_id}_{lecture_id}`

The backend extracts `lecture_id` from the session to load the correct foundational context.

### POST `/chat/{course_id}/clear`

Clear chat history for a session.

**Query Params**: `session_id`

### GET `/chat/{course_id}/history`

Get chat history for a session.

**Query Params**: `session_id`

---

## Troubleshooting

### Issue: Bot gives generic responses to "Next concept.."

**Cause**: The foundational context wasn't loaded (missing lecture_summary in JSON).

**Fix**:
1. Re-run the analyzer to generate the summary:
   ```bash
   python -m pdf_slide_processor.main MS5260 MIS_lec_1-3
   ```
2. Verify the JSON has `lecture_summary` and `key_concepts`
3. Restart the API server

### Issue: Bot loses context after a few exchanges

**Cause**: Memory configuration is too aggressive (token limit too low).

**Fix**: Increase `CHAT_TOKEN_LIMIT` in `.env` to 2000 or higher.

### Issue: Question reformulation not working

**Check the logs**: Look for the `🔄 REFORMULATION STEP` log. If the "Reformulated to" is the same as the original, the LLM didn't detect it as vague.

**Fix**: The few-shot examples in `prompts.py` might need tuning for your specific use case.

---

## Next Steps (Future Enhancements)

1. **Merge RAG API into Main Backend**: Consolidate the two FastAPI servers
2. **RESTful Session API**: Create dedicated `/api/v1/chat/sessions` endpoints for CRUD operations
3. **Persistent Storage**: Save chat history to disk/database instead of in-memory only
4. **Multi-Conversation UI**: Build a ChatGPT-like sidebar with past conversations
5. **Self-Correcting Retrieval**: If a search fails, the bot tries an alternative query

---

## Credits & Philosophy

This system is built on the teaching philosophies of:
- **Richard Feynman**: "If you can't explain it simply, you don't understand it well enough."
- **Walter Lewin**: Make learning an experience, not a lecture.

The three-pillar architecture ensures that every conversation is:
- **Anchored** (Pillar 1: Foundational Context)
- **Coherent** (Pillar 2: Hybrid Memory)
- **Intelligent** (Pillar 3: Context-Aware Reformulation)

---

## License

MIT


