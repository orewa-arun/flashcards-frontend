import asyncio
import logging
import os
from app.db.postgres import init_postgres_db, get_postgres_pool, close_postgres_db
from app.services.mix_session_service import MixSessionService
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_loading():
    try:
        # Initialize DB
        await init_postgres_db()
        pool = await get_postgres_pool()
        
        service = MixSessionService(pool)
        
        course_id = "MAPP_F_MKT404_EN_2025" # From logs
        deck_id = "2" # From logs
        
        print(f"\nTesting loading for Course: {course_id}, Deck: {deck_id}")
        
        # Test loading flashcards (metadata)
        print("\n1. Testing _load_flashcards_for_deck...")
        flashcards = await service._load_flashcards_for_deck(course_id, deck_id)
        print(f"Loaded {len(flashcards)} flashcards")
        if flashcards:
            print(f"Sample flashcard: {flashcards[0]['flashcard_id']}")
            
            # Test loading full content
            fc_id = flashcards[0]['flashcard_id']
            print(f"\n2. Testing _load_flashcard_content for {fc_id}...")
            content = await service._load_flashcard_content(course_id, fc_id)
            if content:
                print("Successfully loaded content")
                print(f"Title/Question: {content.get('question', 'No question')[:50]}...")
            else:
                print("FAILED to load content")
        
        # Test loading questions
        print(f"\n3. Testing _load_questions_for_level (level='medium')...")
        questions = await service._load_questions_for_level(course_id, f"{course_id}_L{deck_id}_FC001", "medium")
        print(f"Loaded {len(questions)} questions")
        if questions:
             print(f"Sample question: {questions[0].get('question_text', '')[:50]}...")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_postgres_db()

if __name__ == "__main__":
    asyncio.run(test_loading())








