"""
Conversational chain implementation with memory.
Enhanced with ConversationSummaryBufferMemory to prevent context drift.
"""
import logging
from typing import Dict, List, Optional
from operator import itemgetter

from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationSummaryBufferMemory

from .prompts import create_contextualize_question_prompt, create_answer_prompt
from .retrievers import CourseTextRetriever
from ..db.vector_store import VectorStore
from ..ingestion.embedder import Embedder
from ..utils.lecture_metadata import load_lecture_metadata, create_foundational_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def format_docs(docs) -> str:
    """
    Format retrieved documents into a single string for the context.
    
    Args:
        docs: List of LangChain Document objects
        
    Returns:
        Formatted string with all document contents
    """
    formatted = []
    for i, doc in enumerate(docs, 1):
        content = f"<document index=\"{i}\">\n"
        content += doc.page_content
        
        # Add metadata for richer context
        metadata = doc.metadata
        if metadata.get("context"):
            content += f"\n[Topic: {metadata['context']}]"
        if metadata.get("tags"):
            content += f"\n[Tags: {', '.join(metadata['tags'])}]"
        
        content += "\n</document>"
        formatted.append(content)
    
    return "\n\n".join(formatted)


def create_conversational_chain(
    course_id: str,
    lecture_id: str,
    vector_store: VectorStore,
    embedder: Embedder,
    llm_model: str = "gemini-1.5-flash-001",
    llm_temperature: float = 0.5,
    top_k: int = 5
):
    """
    Create a conversational RAG chain with history awareness and foundational context.
    
    This chain:
    1. Loads lecture metadata (summary, key concepts) to create foundational context
    2. Takes the chat history and reformulates the question if needed
    3. Retrieves relevant documents from the vector store
    4. Generates an answer using the LLM with the context
    
    Args:
        course_id: Course identifier (e.g., "MS5260")
        lecture_id: Lecture identifier (e.g., "MIS_lec_1-3")
        vector_store: Vector store instance
        embedder: Embedder instance
        llm_model: LLM model name (default: gemini-1.5-flash-001, also try gemini-2.0-flash or gemini-1.5-pro-001)
        llm_temperature: LLM temperature (default: 0.5 for engaging explanations)
        top_k: Number of documents to retrieve
        
    Returns:
        Runnable chain that takes {"input": str, "chat_history": List} and returns answer
    """
    logger.info(f"Creating conversational chain for {course_id}/{lecture_id} with model {llm_model}")
    
    # PILLAR 1: Load lecture metadata and create foundational context
    logger.info(f"Loading lecture metadata for {course_id}/{lecture_id}...")
    metadata = load_lecture_metadata(course_id, lecture_id)
    foundational_context = create_foundational_context(course_id, lecture_id, metadata)
    
    if metadata.get('is_fallback'):
        logger.warning(f"Using fallback metadata for {course_id}/{lecture_id}")
    else:
        logger.info(f"Loaded metadata: {len(metadata.get('key_concepts', []))} key concepts")
    
    logger.debug(f"Foundational context:\n{foundational_context}")
    
    # Initialize LLM (Gemini)
    # IMPORTANT:
    # - Older error logs mentioned v1beta, but the google-generativeai client we use
    #   builds the versioned path itself. The correct way to override is to point
    #   api_endpoint at the bare host (no scheme, no /v1 suffix).
    #   Using a full URL (e.g. 'https://...') confuses DNS resolution
    #   and leads to 'name=https' errors.
    # - Gemini doesn't support SystemMessage, so we convert it to HumanMessage.
    #
    # Valid model names include (depending on your account/region):
    #   - gemini-1.5-flash-001
    #   - gemini-1.5-pro-001
    #   - gemini-2.0-flash
    #   - gemini-2.0-pro
    llm = ChatGoogleGenerativeAI(
        model=llm_model,
        temperature=llm_temperature,
        convert_system_message_to_human=True,
        # Force the client to talk to the correct host; it will add /v1 or /v1beta itself.
        client_options={"api_endpoint": "generativelanguage.googleapis.com"}
    )
    
    # Initialize retriever
    retriever = CourseTextRetriever(
        course_id=course_id,
        vector_store=vector_store,
        embedder=embedder,
        top_k=top_k
    )
    
    # Create a chain that contextualizes the question
    # This reformulates follow-up questions into standalone questions
    # Enhanced with few-shot examples to handle "Next concept", "Tell me more", etc.
    # NOW INCLUDES: Foundational context for intelligent reformulation
    contextualize_question_prompt = create_contextualize_question_prompt(foundational_context)
    contextualize_question_chain = contextualize_question_prompt | llm | StrOutputParser()
    
    # Helper function to log contextualization (PILLAR 3: Enhanced Logging)
    def contextualize_with_logging(x):
        """
        Contextualize the question and log the transformation.
        This is critical for debugging context-aware reformulation.
        """
        original_input = x.get("input", "")
        chat_history = x.get("chat_history", [])
        
        logger.info(f"🔄 REFORMULATION STEP")
        logger.info(f"   Original question: '{original_input}'")
        logger.info(f"   Chat history length: {len(chat_history)} messages")
        
        contextualized = contextualize_question_chain.invoke(x)
        
        if original_input != contextualized:
            logger.info(f"   ✅ Reformulated to: '{contextualized}'")
            logger.info(f"   Reason: Vague follow-up detected, made standalone for vector search")
        else:
            logger.info(f"   ℹ️  No reformulation needed (question already clear)")
        
        return contextualized
    
    # Branch: If there's chat history, contextualize the question. Otherwise, use it as-is.
    contextualized_question = RunnableBranch(
        # If chat_history is not empty, contextualize the question
        (
            lambda x: bool(x.get("chat_history")),
            contextualize_with_logging
        ),
        # Otherwise, just pass through the input
        itemgetter("input")
    )
    
    # Create the retrieval chain
    # This takes the contextualized question and retrieves relevant documents
    retrieval_chain = contextualized_question | retriever
    
    # Create the final answer chain
    # This uses the retrieved documents and chat history to generate an answer
    # NOW INCLUDES: Foundational context pinned to every response
    
    answer_prompt = create_answer_prompt(foundational_context)
    answer_chain = (
        RunnablePassthrough.assign(
            context=retrieval_chain | format_docs
        )
        | answer_prompt
        | llm
        | StrOutputParser()
    )
    
    logger.info("Conversational chain created successfully")
    return answer_chain


class ConversationManager:
    """
    Manages conversation sessions with memory.
    
    This class handles:
    - Creating and managing conversation sessions
    - Storing chat history per session with summarization
    - Invoking the conversational chain
    
    Enhanced with ConversationSummaryBufferMemory to prevent context drift:
    - Keeps recent messages in full detail (PILLAR 2: Hybrid Memory)
    - Summarizes older messages to preserve important context
    - Prevents hallucination when conversations get long
    """
    
    def __init__(
        self,
        course_id: str,
        lecture_id: str,
        vector_store: VectorStore,
        embedder: Embedder,
        llm_model: str = "gemini-1.5-flash-001",
        llm_temperature: float = 0.5,
        top_k: int = 5,
        max_history_messages: int = 6,  # PILLAR 2: Keep last 6 messages in full detail (3 user + 3 AI)
        max_token_limit: int = 1500  # PILLAR 2: Larger buffer for better context retention
    ):
        """
        Initialize the conversation manager.
        
        Args:
            course_id: Course identifier (e.g., "MS5260")
            lecture_id: Lecture identifier (e.g., "MIS_lec_1-3")
            vector_store: Vector store instance
            embedder: Embedder instance
            llm_model: LLM model name
            llm_temperature: LLM temperature
            top_k: Number of documents to retrieve
            max_history_messages: Number of recent messages to keep in full detail
            max_token_limit: Token limit before older messages are summarized
        """
        self.course_id = course_id
        self.lecture_id = lecture_id
        self.max_history_messages = max_history_messages
        self.llm_model = llm_model
        self.max_token_limit = max_token_limit
        
        # Initialize LLM for summarization
        self.llm = ChatGoogleGenerativeAI(
            model=llm_model,
            temperature=llm_temperature,
            convert_system_message_to_human=True,
            client_options={"api_endpoint": "generativelanguage.googleapis.com"}
        )
        
        # Create the conversational chain (with PILLAR 1: Foundational Context)
        self.chain = create_conversational_chain(
            course_id=course_id,
            lecture_id=lecture_id,
            vector_store=vector_store,
            embedder=embedder,
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            top_k=top_k
        )
        
        # Store conversation memories by session_id (using LangChain's memory)
        self.session_memories: Dict[str, ConversationSummaryBufferMemory] = {}
    
    def get_or_create_memory(self, session_id: str) -> ConversationSummaryBufferMemory:
        """
        Get or create a conversation memory for a session.
        
        PILLAR 2: Hybrid Memory Implementation
        Uses ConversationSummaryBufferMemory which:
        - Keeps recent 6 messages (3 exchanges) in full detail for perfect short-term recall
        - Summarizes older messages when token limit (1500) is exceeded
        - Prevents context drift in long conversations
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ConversationSummaryBufferMemory instance for the session
        """
        if session_id not in self.session_memories:
            logger.info(f"Creating new memory for session {session_id} with summarization")
            self.session_memories[session_id] = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=self.max_token_limit,
                return_messages=True,
                memory_key="chat_history"
            )
        return self.session_memories[session_id]
    
    def chat(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, str]:
        """
        Process a chat message and return the response.
        
        Uses ConversationSummaryBufferMemory to maintain context:
        - Recent messages are kept in full detail
        - Older messages are automatically summarized
        - Prevents hallucination in long conversations
        
        Args:
            session_id: Unique session identifier
            message: User's message
            
        Returns:
            Dictionary with 'answer' and 'session_id'
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"💬 NEW MESSAGE | Session: {session_id}")
        logger.info(f"   User said: '{message}'")
        logger.info(f"{'='*70}")
        
        # Get memory for this session
        memory = self.get_or_create_memory(session_id)
        
        # Load chat history from memory (PILLAR 2: Hybrid Memory)
        # This returns a mix of: summary of old messages + recent full messages
        raw_chat_history = memory.load_memory_variables({}).get("chat_history", [])
        
        # Filter out SystemMessage objects - they cause errors in ChatGoogleGenerativeAI
        # Only keep HumanMessage and AIMessage for the prompt template
        chat_history = [
            msg for msg in raw_chat_history 
            if isinstance(msg, (HumanMessage, AIMessage))
        ]
        
        logger.info(f"📚 MEMORY | Loaded {len(raw_chat_history)} messages, filtered to {len(chat_history)} (Human/AI only)")
        
        # Log recent chat history for debugging
        if chat_history:
            logger.info(f"📜 RECENT HISTORY (last 4 messages):")
            for i, msg in enumerate(chat_history[-4:], 1):
                role = "👤 User" if isinstance(msg, HumanMessage) else "🤖 Assistant"
                preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                logger.info(f"   {role}: {preview}")
        
        # Invoke the chain with the filtered history
        # The chain will: 1) Contextualize question (PILLAR 3), 2) Retrieve docs, 3) Generate answer (PILLAR 1)
        logger.info(f"\n🚀 INVOKING CHAIN...")
        response = self.chain.invoke({
            "input": message,
            "chat_history": chat_history
        })
        
        logger.info(f"\n✅ RESPONSE GENERATED")
        logger.info(f"   Length: {len(response)} characters")
        logger.info(f"   Preview: {response[:150]}...")
        
        # Save the interaction to memory (PILLAR 2: Hybrid Memory)
        # Memory will automatically handle summarization if needed
        memory.save_context(
            {"input": message},
            {"output": response}
        )
        logger.info(f"💾 Interaction saved to memory")
        logger.info(f"{'='*70}\n")
        
        logger.info(f"Generated response (length: {len(response)}), saved to memory")
        
        return {
            "answer": response,
            "session_id": session_id
        }
    
    def clear_session(self, session_id: str):
        """
        Clear the chat history for a session.
        
        Args:
            session_id: Session identifier to clear
        """
        if session_id in self.session_memories:
            # Clear the memory
            self.session_memories[session_id].clear()
            logger.info(f"Cleared memory for session {session_id}")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get the chat history for a session in a readable format.
        
        Returns the memory-managed history which includes:
        - Summary of older messages (if conversation is long)
        - Full text of recent messages
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        memory = self.get_or_create_memory(session_id)
        chat_history = memory.load_memory_variables({}).get("chat_history", [])
        
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                formatted_history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_history.append({"role": "assistant", "content": msg.content})
        
        return formatted_history

