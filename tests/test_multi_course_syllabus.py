"""Regression tests verifying dynamic syllabus parsing across multiple distinct subjects."""

from course_automation.sites.codechef.syllabus import CodeChefSyllabusParser
from course_automation.storage.models import ActivityStatus, ActivityType


def test_java_oops_course():
    """Subject 1: Java Object-Oriented Programming (Semester 3)."""
    payload = {
        "course_id": "cu-oops-sem3-2026-c2",
        "course_name": "Object Oriented Programming in Java",
        "modules": [
            {
                "id": "unit_1",
                "name": "Unit 1: Classes & Methods",
                "slug": "unit-1-classes",
                "activities": [
                    {"id": "JAVA01", "name": "Class Basics", "type": "PROBLEM", "status": "COMPLETED", "language": "java"},
                    {"id": "JAVA02", "name": "Encapsulation", "type": "PROBLEM", "status": "COMPLETED", "language": "java"},
                ],
            },
            {
                "id": "unit_3",
                "name": "Unit 3: Java GUI & JDBC",
                "slug": "unit-3-gui",
                "activities": [
                    {"id": "JDBCAPILAB02", "name": "Display Course Names", "type": "PROBLEM", "status": "IN_PROGRESS", "language": "java"},
                    {"id": "JAVAGUILAB", "name": "Movie Ticket Booking", "type": "PROBLEM", "status": "NOT_STARTED", "language": "java"},
                ],
            },
        ],
    }
    url = "https://www.codechef.com/learn/course/cu-oops-sem3-2026-c2"
    summary = CodeChefSyllabusParser.parse_api_data(payload, url, "cu-oops-sem3-2026-c2")

    assert summary.title == "Object Oriented Programming in Java"
    assert summary.total_activities == 4
    assert summary.completed_activities == 2
    assert summary.progress_percentage == 50.0
    assert summary.modules[1].activities[0].language == "java"


def test_cpp_adsa_course():
    """Subject 2: C++ Advanced Data Structures & Algorithms."""
    payload = {
        "course_id": "cu-adsa-sem3-2026-c2",
        "course_name": "Advanced Data Structures and Algorithms",
        "modules": [
            {
                "id": "sort_unit",
                "name": "Sorting Algorithms",
                "slug": "sorting",
                "activities": [
                    {"id": "INSSRTASCD", "name": "Insertion Sort", "type": "PROBLEM", "status": "COMPLETED", "language": "cpp"},
                    {"id": "SESO44", "name": "Quick Sort", "type": "PROBLEM", "status": "COMPLETED", "language": "cpp"},
                    {"id": "ONP", "name": "Transform Expression", "type": "PROBLEM", "status": "NOT_STARTED", "language": "cpp"},
                ],
            }
        ],
    }
    url = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-c2"
    summary = CodeChefSyllabusParser.parse_api_data(payload, url, "cu-adsa-sem3-2026-c2")

    assert summary.title == "Advanced Data Structures and Algorithms"
    assert summary.total_activities == 3
    assert summary.completed_activities == 2
    assert summary.progress_percentage == 66.7
    assert summary.modules[0].activities[0].language == "cpp"


def test_c_datastructures_course():
    """Subject 3: C Data Structures."""
    payload = {
        "course_id": "cu-adsa-sem3-2026-b1",
        "course_name": "Data Structures in C",
        "modules": [
            {
                "id": "trees_unit",
                "name": "Binary Search Trees",
                "slug": "bst",
                "activities": [
                    {"id": "BSTIMP", "name": "BST Implementation", "type": "PROBLEM", "status": "COMPLETED", "language": "c"},
                ],
            }
        ],
    }
    url = "https://www.codechef.com/learn/course/cu-adsa-sem3-2026-b1"
    summary = CodeChefSyllabusParser.parse_api_data(payload, url, "cu-adsa-sem3-2026-b1")

    assert summary.title == "Data Structures in C"
    assert summary.total_activities == 1
    assert summary.completed_activities == 1
    assert summary.progress_percentage == 100.0


def test_python_basics_course():
    """Subject 4: Learn Python Course."""
    payload = {
        "course_id": "python",
        "course_name": "Python for Beginners",
        "modules": [
            {
                "id": "py_intro",
                "name": "Introduction to Python",
                "slug": "intro",
                "activities": [
                    {"id": "PYTH01", "name": "Printing Output", "type": "PROBLEM", "status": "COMPLETED", "language": "python3"},
                    {"id": "PYTH02", "name": "Variables & Types", "type": "PROBLEM", "status": "NOT_STARTED", "language": "python3"},
                ],
            }
        ],
    }
    url = "https://www.codechef.com/learn/course/python"
    summary = CodeChefSyllabusParser.parse_api_data(payload, url, "python")

    assert summary.title == "Python for Beginners"
    assert summary.total_activities == 2
    assert summary.completed_activities == 1
    assert summary.progress_percentage == 50.0
    assert summary.modules[0].activities[0].language == "python3"
