"""Pytest shared fixtures."""

import os
import pytest
from pathlib import Path

@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_progress.db"

@pytest.fixture
def sample_syllabus_payload():
    return {
        "course_id": "test-course-101",
        "course_name": "Object Oriented Programming in Java",
        "modules": [
            {
                "id": "mod_1",
                "name": "Unit 1: Classes & Objects",
                "slug": "classes-objects",
                "activities": [
                    {
                        "id": "act_1",
                        "name": "Introduction to Classes",
                        "type": "THEORY",
                        "status": "COMPLETED",
                        "url": "https://www.codechef.com/learn/course/test-course-101/classes-objects/lesson/intro",
                    },
                    {
                        "id": "act_2",
                        "name": "Create a Rectangle Class",
                        "type": "PROBLEM",
                        "status": "NOT_STARTED",
                        "language": "java",
                        "url": "https://www.codechef.com/learn/course/test-course-101/classes-objects/problems/RECT01",
                    },
                ],
            },
            {
                "id": "mod_2",
                "name": "Unit 2: Inheritance",
                "slug": "inheritance",
                "activities": [
                    {
                        "id": "act_3",
                        "name": "Inheritance Quiz",
                        "type": "QUIZ",
                        "status": "IN_PROGRESS",
                        "url": "https://www.codechef.com/learn/course/test-course-101/inheritance/lesson/quiz1",
                    }
                ],
            },
        ],
    }
