#!/usr/bin/env python3
"""
Quick diagnostic script to check exam configuration vs quiz attempts.
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME')]

def check_exam_config(course_id='MS5150'):
    print(f"=== EXAM CONFIGURATION FOR {course_id} ===\n")
    
    # Get the timetable
    timetable = db.timetables.find_one({'course_id': course_id})
    if not timetable:
        print(f"❌ No timetable found for {course_id}")
        return
    
    exams = timetable.get('exams', [])
    if not exams:
        print(f"❌ No exams configured for {course_id}")
        return
    
    for exam in exams:
        exam_id = exam.get('exam_id', 'Unknown')
        exam_name = exam.get('name', 'Unknown')
        lectures = exam.get('lectures', [])
        
        print(f"📝 Exam: {exam_name} (ID: {exam_id})")
        print(f"   Covered Lectures: {lectures}")
        print()
    
    print("\n=== RECENT QUIZ ATTEMPTS ===\n")
    
    # Get recent quiz results
    results = list(db.quiz_results.find({'course_id': course_id}).sort('completed_at', -1).limit(10))
    
    if not results:
        print(f"❌ No quiz attempts found for {course_id}")
        return
    
    lecture_counts = {}
    for r in results:
        lecture_id = r.get('lecture_id', 'Unknown')
        lecture_counts[lecture_id] = lecture_counts.get(lecture_id, 0) + 1
    
    print("Quiz attempts by lecture:")
    for lecture_id, count in sorted(lecture_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {lecture_id}: {count} attempts")
    
    print("\n=== DIAGNOSIS ===\n")
    
    # Check for mismatches
    all_exam_lectures = set()
    for exam in exams:
        all_exam_lectures.update(exam.get('lectures', []))
    
    quiz_lectures = set(lecture_counts.keys())
    
    missing_in_exam = quiz_lectures - all_exam_lectures
    if missing_in_exam:
        print(f"⚠️  WARNING: You took quizzes on these lectures, but they're NOT in any exam:")
        for lec in missing_in_exam:
            print(f"   - {lec}")
        print("\n   These quiz attempts will NOT count toward exam readiness!")
        print("   Solution: Add these lectures to your exam configuration in 'My Schedule'")
    else:
        print("✅ All quiz attempts are on lectures covered by exams")

if __name__ == "__main__":
    course_id = sys.argv[1] if len(sys.argv) > 1 else 'MS5150'
    check_exam_config(course_id)

