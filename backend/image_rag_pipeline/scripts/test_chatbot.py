# """
# Test script for the conversational chatbot.

# This script tests the chatbot functionality without requiring an OpenAI API key.
# For full testing with real LLM responses, set OPENAI_API_KEY environment variable.
# """
# import os
# import sys

# # Add parent directory to path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# from app.db.vector_store import VectorStore
# from app.ingestion.embedder import Embedder
# from app.utils.config import Config


# def test_imports():
#     """Test that all chatbot modules can be imported."""
#     print("\n" + "="*60)
#     print("TEST 1: Checking imports...")
#     print("="*60)
    
#     try:
#         from app.chatbot.retrievers import CourseTextRetriever
#         print("✓ CourseTextRetriever imported successfully")
#     except ImportError as e:
#         print(f"✗ Failed to import CourseTextRetriever: {e}")
#         return False
    
#     try:
#         from app.chatbot.prompts import contextualize_question_prompt, answer_prompt
#         print("✓ Prompts imported successfully")
#     except ImportError as e:
#         print(f"✗ Failed to import prompts: {e}")
#         return False
    
#     try:
#         from app.chatbot.chain import ConversationManager, create_conversational_chain
#         print("✓ ConversationManager imported successfully")
#     except ImportError as e:
#         print(f"✗ Failed to import ConversationManager: {e}")
#         return False
    
#     try:
#         from app.chatbot.gradio_app import create_chatbot_ui
#         print("✓ Gradio app imported successfully")
#     except ImportError as e:
#         print(f"✗ Failed to import Gradio app: {e}")
#         return False
    
#     return True


# def test_retriever():
#     """Test the LangChain retriever wrapper."""
#     print("\n" + "="*60)
#     print("TEST 2: Testing CourseTextRetriever...")
#     print("="*60)
    
#     try:
#         from app.chatbot.retrievers import CourseTextRetriever
        
#         # Initialize components
#         base_dir = os.path.join(os.path.dirname(__file__), "..")
#         vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        
#         if not os.path.exists(vector_db_path):
#             print(f"⚠ Vector database not found at {vector_db_path}")
#             print("  Run batch_ingest.py first to create the database")
#             return True  # Not a failure, just not set up yet
        
#         vector_store = VectorStore(path=vector_db_path)
#         embedder = Embedder(
#             model_name=Config.CLIP_MODEL,
#             pretrained=Config.CLIP_PRETRAINED
#         )
        
#         retriever = CourseTextRetriever(
#             course_id="MS5260",
#             vector_store=vector_store,
#             embedder=embedder,
#             top_k=3
#         )
        
#         print("✓ CourseTextRetriever initialized successfully")
        
#         # Test retrieval (requires data to be ingested)
#         try:
#             query = "What is MIS?"
#             docs = retriever._get_relevant_documents(query)
#             print(f"✓ Retrieved {len(docs)} documents for query: '{query}'")
            
#             if docs:
#                 print(f"  First result: {docs[0].page_content[:100]}...")
#         except Exception as e:
#             print(f"⚠ Retrieval test skipped (no data ingested): {e}")
        
#         return True
        
#     except Exception as e:
#         print(f"✗ Error testing retriever: {e}")
#         import traceback
#         traceback.print_exc()
#         return False


# def test_conversation_manager_init():
#     """Test ConversationManager initialization."""
#     print("\n" + "="*60)
#     print("TEST 3: Testing ConversationManager initialization...")
#     print("="*60)
    
#     if not os.getenv("OPENAI_API_KEY"):
#         print("⚠ OPENAI_API_KEY not set, skipping ConversationManager test")
#         print("  Set the environment variable to test full functionality:")
#         print("    export OPENAI_API_KEY='sk-your-key-here'")
#         return True
    
#     try:
#         from app.chatbot.chain import ConversationManager
        
#         base_dir = os.path.join(os.path.dirname(__file__), "..")
#         vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        
#         if not os.path.exists(vector_db_path):
#             print(f"⚠ Vector database not found at {vector_db_path}")
#             return True
        
#         vector_store = VectorStore(path=vector_db_path)
#         embedder = Embedder()
        
#         manager = ConversationManager(
#             course_id="MS5260",
#             vector_store=vector_store,
#             embedder=embedder
#         )
        
#         print("✓ ConversationManager initialized successfully")
        
#         # Test session management
#         session_id = "test_session"
#         history = manager.get_session_history(session_id)
#         print(f"✓ Session history retrieved: {len(history)} messages")
        
#         return True
        
#     except Exception as e:
#         print(f"✗ Error testing ConversationManager: {e}")
#         import traceback
#         traceback.print_exc()
#         return False


# def test_api_endpoints():
#     """Test that the API server has the chat endpoints."""
#     print("\n" + "="*60)
#     print("TEST 4: Checking API endpoints...")
#     print("="*60)
    
#     try:
#         from app.api.server import app
        
#         routes = [route.path for route in app.routes]
        
#         required_endpoints = [
#             "/chat/{course_id}",
#             "/chat/{course_id}/clear",
#             "/chat/{course_id}/history"
#         ]
        
#         for endpoint in required_endpoints:
#             if endpoint in routes:
#                 print(f"✓ Endpoint {endpoint} registered")
#             else:
#                 print(f"✗ Endpoint {endpoint} not found")
#                 return False
        
#         return True
        
#     except Exception as e:
#         print(f"✗ Error checking endpoints: {e}")
#         return False


# def main():
#     """Run all tests."""
#     print("\n" + "="*60)
#     print("CHATBOT FUNCTIONALITY TESTS")
#     print("="*60)
    
#     tests = [
#         ("Imports", test_imports),
#         ("Retriever", test_retriever),
#         ("Conversation Manager", test_conversation_manager_init),
#         ("API Endpoints", test_api_endpoints),
#     ]
    
#     results = []
#     for name, test_func in tests:
#         try:
#             result = test_func()
#             results.append((name, result))
#         except Exception as e:
#             print(f"\n✗ Test '{name}' crashed: {e}")
#             results.append((name, False))
    
#     # Summary
#     print("\n" + "="*60)
#     print("TEST SUMMARY")
#     print("="*60)
    
#     for name, passed in results:
#         status = "✓ PASS" if passed else "✗ FAIL"
#         print(f"{status}: {name}")
    
#     all_passed = all(result for _, result in results)
    
#     if all_passed:
#         print("\n✓ All tests passed!")
#         print("\nNext steps:")
#         print("1. Install dependencies: pip install langchain langchain-core langchain-openai gradio")
#         print("2. Set OPENAI_API_KEY: export OPENAI_API_KEY='sk-your-key-here'")
#         print("3. Run batch ingestion: python scripts/batch_ingest.py --course-id MS5260")
#         print("4. Launch Gradio UI: python -m app.chatbot.gradio_app --course-id MS5260")
#         print("   OR")
#         print("   Start FastAPI server: python -m app.api.server")
#     else:
#         print("\n✗ Some tests failed. Check the output above for details.")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()

