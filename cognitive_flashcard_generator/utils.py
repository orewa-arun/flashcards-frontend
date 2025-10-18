"""
Utility functions for course management.
"""

import os
import json
from typing import Dict, List, Any, Optional


def load_courses(courses_file: str = "courses_resources/courses.json") -> List[Dict[str, Any]]:
    """
    Load course configurations from courses.json.
    
    Args:
        courses_file: Path to courses.json file
        
    Returns:
        List of course dictionaries
    """
    if not os.path.exists(courses_file):
        print(f"❌ Error: {courses_file} not found!")
        print(f"   Please create a courses.json file with your course configurations.")
        return []
    
    with open(courses_file, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    
    return courses


def get_course_by_id(course_id: str, courses: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Get a specific course by its ID.
    
    Args:
        course_id: The course ID to search for
        courses: List of all courses
        
    Returns:
        Course dictionary or None if not found
    """
    for course in courses:
        if course.get('course_id') == course_id:
            return course
    return None

