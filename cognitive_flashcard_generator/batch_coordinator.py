"""
Batch Coordinator - Manages concurrent API calls for flashcard and quiz generation.
"""

import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime

from .async_generator import AsyncCognitiveFlashcardGenerator
from .async_quiz_generator import AsyncQuizGenerator


class BatchCoordinator:
    """Coordinates batched generation of flashcards and quizzes."""
    
    def __init__(self, max_concurrent_requests: int = 10):
        """
        Initialize the batch coordinator.
        
        Args:
            max_concurrent_requests: Maximum number of concurrent API requests
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def _rate_limited_task(self, coro):
        """Execute a coroutine with rate limiting."""
        async with self.semaphore:
            return await coro
    
    async def batch_generate_flashcards(
        self,
        generator: AsyncCognitiveFlashcardGenerator,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate flashcards for multiple chunks concurrently.
        
        Args:
            generator: AsyncCognitiveFlashcardGenerator instance
            tasks: List of task dictionaries with keys:
                   - content: str
                   - source_name: str
                   - chunk_info: str
                   - task_id: str
        
        Returns:
            List of result dictionaries
        """
        print(f"\n{'='*80}")
        print(f"🚀 BATCH FLASHCARD GENERATION")
        print(f"{'='*80}")
        print(f"📊 Total tasks: {len(tasks)}")
        print(f"⚡ Max concurrent requests: {self.max_concurrent_requests}")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        # Create coroutines for all tasks
        coroutines = [
            self._rate_limited_task(
                generator.generate_flashcards_async(
                    content=task['content'],
                    source_name=task['source_name'],
                    chunk_info=task['chunk_info'],
                    task_id=task['task_id']
                )
            )
            for task in tasks
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Process results
        successful = 0
        failed = 0
        total_flashcards = 0
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Task failed with exception: {result}")
                failed += 1
            elif isinstance(result, dict):
                processed_results.append(result)
                if result['success']:
                    successful += 1
                    total_flashcards += len(result['flashcards'])
                else:
                    failed += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"✅ BATCH FLASHCARD GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Successful: {successful}/{len(tasks)}")
        print(f"❌ Failed: {failed}/{len(tasks)}")
        print(f"📝 Total flashcards generated: {total_flashcards}")
        print(f"⚡ Average speed: {len(tasks)/duration:.2f} tasks/second")
        print(f"{'='*80}\n")
        
        return processed_results
    
    async def batch_generate_quizzes(
        self,
        generator: AsyncQuizGenerator,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions for multiple chunks and levels concurrently.
        
        Args:
            generator: AsyncQuizGenerator instance
            tasks: List of task dictionaries with keys:
                   - flashcards_chunk: List[Dict]
                   - level: int
                   - chunk_info: str
                   - task_id: str
        
        Returns:
            List of result dictionaries
        """
        print(f"\n{'='*80}")
        print(f"🚀 BATCH QUIZ GENERATION")
        print(f"{'='*80}")
        print(f"📊 Total tasks: {len(tasks)}")
        print(f"⚡ Max concurrent requests: {self.max_concurrent_requests}")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        # Create coroutines for all tasks
        coroutines = [
            self._rate_limited_task(
                generator.generate_quiz_questions_async(
                    flashcards_chunk=task['flashcards_chunk'],
                    level=task['level'],
                    chunk_info=task['chunk_info'],
                    task_id=task['task_id']
                )
            )
            for task in tasks
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Process results
        successful = 0
        failed = 0
        total_questions = 0
        
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ Task failed with exception: {result}")
                failed += 1
            elif isinstance(result, dict):
                processed_results.append(result)
                if result['success']:
                    successful += 1
                    total_questions += len(result['questions'])
                else:
                    failed += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"✅ BATCH QUIZ GENERATION COMPLETE")
        print(f"{'='*80}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Successful: {successful}/{len(tasks)}")
        print(f"❌ Failed: {failed}/{len(tasks)}")
        print(f"📝 Total questions generated: {total_questions}")
        print(f"⚡ Average speed: {len(tasks)/duration:.2f} tasks/second")
        print(f"{'='*80}\n")
        
        return processed_results
    
    async def batch_generate_all(
        self,
        flashcard_generator: AsyncCognitiveFlashcardGenerator,
        quiz_generator: AsyncQuizGenerator,
        flashcard_tasks: List[Dict[str, Any]],
        quiz_tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate both flashcards and quizzes concurrently.
        
        Args:
            flashcard_generator: AsyncCognitiveFlashcardGenerator instance
            quiz_generator: AsyncQuizGenerator instance
            flashcard_tasks: List of flashcard task dictionaries
            quiz_tasks: List of quiz task dictionaries
        
        Returns:
            Tuple of (flashcard_results, quiz_results)
        """
        print(f"\n{'='*80}")
        print(f"🚀 BATCH GENERATION - FLASHCARDS + QUIZZES")
        print(f"{'='*80}")
        print(f"📊 Total flashcard tasks: {len(flashcard_tasks)}")
        print(f"📊 Total quiz tasks: {len(quiz_tasks)}")
        print(f"📊 Total tasks: {len(flashcard_tasks) + len(quiz_tasks)}")
        print(f"⚡ Max concurrent requests: {self.max_concurrent_requests}")
        print(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        # Run both batches concurrently
        flashcard_results, quiz_results = await asyncio.gather(
            self.batch_generate_flashcards(flashcard_generator, flashcard_tasks),
            self.batch_generate_quizzes(quiz_generator, quiz_tasks)
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_tasks = len(flashcard_tasks) + len(quiz_tasks)
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETE BATCH GENERATION FINISHED")
        print(f"{'='*80}")
        print(f"⏱️  Total Duration: {duration:.2f} seconds")
        print(f"📊 Total tasks completed: {total_tasks}")
        print(f"⚡ Overall speed: {total_tasks/duration:.2f} tasks/second")
        print(f"{'='*80}\n")
        
        return flashcard_results, quiz_results


def run_batch_generation(
    flashcard_generator: AsyncCognitiveFlashcardGenerator,
    quiz_generator: AsyncQuizGenerator,
    flashcard_tasks: List[Dict[str, Any]],
    quiz_tasks: List[Dict[str, Any]],
    max_concurrent: int = 10
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function to run batch generation in a synchronous context.
    
    Args:
        flashcard_generator: AsyncCognitiveFlashcardGenerator instance
        quiz_generator: AsyncQuizGenerator instance
        flashcard_tasks: List of flashcard task dictionaries
        quiz_tasks: List of quiz task dictionaries
        max_concurrent: Maximum number of concurrent requests
    
    Returns:
        Tuple of (flashcard_results, quiz_results)
    """
    coordinator = BatchCoordinator(max_concurrent_requests=max_concurrent)
    
    # Run the async batch generation
    return asyncio.run(
        coordinator.batch_generate_all(
            flashcard_generator,
            quiz_generator,
            flashcard_tasks,
            quiz_tasks
        )
    )

