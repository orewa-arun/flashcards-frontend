#!/usr/bin/env python3
"""
Test script for the adaptive quiz API endpoints.
Run this after starting the backend server to verify everything works.
"""

import requests
import json
from uuid import uuid4

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = str(uuid4())
COURSE_ID = "MS5260"
DECK_ID = "MIS_lec_4"

def test_quiz_generation():
    """Test the quiz generation endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Quiz Generation")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/quiz/generate"
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER_ID
    }
    data = {
        "course_id": COURSE_ID,
        "deck_id": DECK_ID,
        "num_questions": 20
    }
    
    print(f"\nGenerating quiz for user: {TEST_USER_ID}")
    print(f"Course: {COURSE_ID}, Deck: {DECK_ID}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ Quiz generated successfully!")
        print(f"   Quiz ID: {result['quiz_id']}")
        print(f"   Total Questions: {result['total_questions']}")
        print(f"   Quiz Attempt #: {result['quiz_attempt_number']}")
        print(f"\nFirst 3 questions:")
        for i, question in enumerate(result['questions'][:3], 1):
            print(f"\n   {i}. [{question['question_type']}] {question['concept_context']}")
            print(f"      Relevance: {question['relevance_score']}/10")
            print(f"      Question: {question['question'][:80]}...")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error generating quiz: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def test_quiz_submission(quiz_data):
    """Test the quiz submission endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Quiz Submission")
    print("="*60)
    
    if not quiz_data:
        print("❌ Skipping submission test (no quiz data)")
        return
    
    url = f"{BASE_URL}/api/v1/quiz/submit"
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER_ID
    }
    
    # Create sample answers (50% correct, 50% incorrect for testing)
    answers = []
    for i, question in enumerate(quiz_data['questions']):
        if i % 2 == 0:
            # Correct answer
            user_answer = question['correct_answer']
        else:
            # Incorrect answer (use a dummy value)
            if question['question_type'] in ['mcq', 'scenario_mcq']:
                user_answer = "Incorrect option"
            elif question['question_type'] == 'sequencing':
                # Reverse the correct order
                user_answer = list(reversed(question['correct_answer']))
            else:
                user_answer = {}
        
        answers.append({
            "question_id": question['question_id'],
            "user_answer": user_answer
        })
    
    data = {
        "quiz_id": quiz_data['quiz_id'],
        "course_id": COURSE_ID,
        "deck_id": DECK_ID,
        "answers": answers,
        "time_taken_seconds": 300
    }
    
    print(f"\nSubmitting quiz with {len(answers)} answers...")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ Quiz submitted successfully!")
        print(f"   Score: {result['score']}/{result['total_questions']} ({result['percentage']:.1f}%)")
        print(f"   Time Taken: {result['time_taken_seconds']}s")
        print(f"   Quiz Attempt #: {result['quiz_attempt_number']}")
        
        if result['weak_concepts']:
            print(f"\n📚 Weak Concepts to Review ({len(result['weak_concepts'])}):")
            for concept in result['weak_concepts'][:5]:
                print(f"   • {concept['concept_context']}")
                print(f"     Accuracy: {concept['accuracy']:.1f}% ({concept['times_correct']}/{concept['times_attempted']})")
        else:
            print("\n🌟 No weak concepts - Great job!")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error submitting quiz: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def test_adaptive_quiz_generation():
    """Test that the second quiz adapts based on first quiz performance."""
    print("\n" + "="*60)
    print("TEST 3: Adaptive Quiz Generation (Second Attempt)")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/quiz/generate"
    headers = {
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER_ID
    }
    data = {
        "course_id": COURSE_ID,
        "deck_id": DECK_ID,
        "num_questions": 20
    }
    
    print(f"\nGenerating second quiz for user: {TEST_USER_ID}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"\n✅ Second quiz generated successfully!")
        print(f"   Quiz ID: {result['quiz_id']}")
        print(f"   Quiz Attempt #: {result['quiz_attempt_number']}")
        print(f"\n   This quiz should prioritize:")
        print(f"   1. Concepts answered incorrectly in previous quiz")
        print(f"   2. Concepts not yet attempted")
        print(f"   3. Concepts answered correctly (for reinforcement)")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error generating second quiz: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ADAPTIVE QUIZ ENGINE - API TEST SUITE")
    print("="*60)
    print(f"\nBackend URL: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    
    # Test 1: Generate first quiz
    quiz_data = test_quiz_generation()
    
    # Test 2: Submit quiz with mixed results
    if quiz_data:
        submission_result = test_quiz_submission(quiz_data)
        
        # Test 3: Generate second quiz (should be adaptive)
        if submission_result:
            test_adaptive_quiz_generation()
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

