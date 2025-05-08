from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db():
    """Get database connection"""
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    return client[os.getenv('MONGO_DBNAME', 'CSELEC3DB')]

def calculate_gpa(weighted_average: float) -> float:
    """Calculate GPA from weighted average"""
    if weighted_average >= 97: return 4.0
    elif weighted_average >= 94: return 3.75
    elif weighted_average >= 91: return 3.5
    elif weighted_average >= 88: return 3.25
    elif weighted_average >= 85: return 3.0
    elif weighted_average >= 82: return 2.75
    elif weighted_average >= 79: return 2.5
    elif weighted_average >= 76: return 2.25
    elif weighted_average >= 73: return 2.0
    elif weighted_average >= 70: return 1.75
    elif weighted_average >= 67: return 1.5
    elif weighted_average >= 64: return 1.25
    elif weighted_average >= 60: return 1.0
    else: return 0.0

def get_academic_standing(gpa: float) -> str:
    """Determine academic standing based on GPA"""
    if gpa >= 3.0: return "good"
    elif gpa >= 2.0: return "warning"
    elif gpa >= 1.0: return "probation"
    else: return "dismissed"

def update_student_averages(student_id: int, semester_id: int) -> Dict[str, Any]:
    """Update student averages for a semester"""
    db = get_db()
    
    # Get all grades for the student in the semester
    grades = list(db.grades.find({
        "student_id": student_id,
        "semester_id": semester_id,
        "status": "finalized"
    }))
    
    if not grades:
        return None
    
    # Calculate weighted average
    total_units = 0
    weighted_sum = 0
    
    for grade_doc in grades:
        for i, subject_code in enumerate(grade_doc['subject_codes']):
            subject = db.subjects.find_one({"id": subject_code})
            if subject:
                units = subject['units']
                grade = grade_doc['grades'][i]
                total_units += units
                weighted_sum += grade * units
    
    weighted_average = weighted_sum / total_units if total_units > 0 else 0
    
    # Update student_averages
    result = db.student_averages.update_one(
        {"student_id": student_id, "semester_id": semester_id},
        {
            "$set": {
                "weighted_average": weighted_average,
                "total_units": total_units,
                "subjects_taken": len(grades),
                "updated_at": datetime.now()
            }
        },
        upsert=True
    )
    
    return {
        "student_id": student_id,
        "semester_id": semester_id,
        "weighted_average": weighted_average,
        "total_units": total_units,
        "subjects_taken": len(grades)
    }

def update_class_averages(subject_code: str, semester_id: int) -> Dict[str, Any]:
    """Update class averages for a subject in a semester"""
    db = get_db()
    
    # Get all grades for the subject in the semester
    grades = list(db.grades.find({
        "semester_id": semester_id,
        "subject_codes": subject_code,
        "status": "finalized"
    }))
    
    if not grades:
        return None
    
    # Calculate statistics
    all_grades = []
    for grade_doc in grades:
        idx = grade_doc['subject_codes'].index(subject_code)
        all_grades.append(grade_doc['grades'][idx])
    
    total_students = len(all_grades)
    average_grade = sum(all_grades) / total_students
    passing_count = sum(1 for g in all_grades if g >= 75)
    at_risk_count = sum(1 for g in all_grades if g < 75)
    
    # Calculate grade distribution
    distribution = {
        "A": sum(1 for g in all_grades if g >= 97),
        "B": sum(1 for g in all_grades if 94 <= g < 97),
        "C": sum(1 for g in all_grades if 91 <= g < 94),
        "D": sum(1 for g in all_grades if 88 <= g < 91),
        "F": sum(1 for g in all_grades if g < 88)
    }
    
    subject = db.subjects.find_one({"id": subject_code})
    
    # Update class_averages
    result = db.class_averages.update_one(
        {"subject_code": subject_code, "semester_id": semester_id},
        {
            "$set": {
                "average_grade": average_grade,
                "passing_rate": (passing_count / total_students) * 100,
                "at_risk_rate": (at_risk_count / total_students) * 100,
                "top_grade": max(all_grades),
                "grade_distribution": distribution,
                "total_students": total_students,
                "subject_description": subject['description'] if subject else "",
                "updated_at": datetime.now()
            }
        },
        upsert=True
    )
    
    return {
        "subject_code": subject_code,
        "semester_id": semester_id,
        "average_grade": average_grade,
        "passing_rate": (passing_count / total_students) * 100,
        "at_risk_rate": (at_risk_count / total_students) * 100,
        "total_students": total_students
    }

def update_student_gpa(student_id: int, semester_id: int) -> Dict[str, Any]:
    """Update student GPA for a semester"""
    db = get_db()
    
    # Get student average
    student_avg = db.student_averages.find_one({
        "student_id": student_id,
        "semester_id": semester_id
    })
    
    if not student_avg:
        return None
    
    weighted_average = student_avg['weighted_average']
    gpa = calculate_gpa(weighted_average)
    academic_standing = get_academic_standing(gpa)
    
    # Update student_gpas
    result = db.student_gpas.update_one(
        {"student_id": student_id, "semester_id": semester_id},
        {
            "$set": {
                "weighted_average": weighted_average,
                "gpa": gpa,
                "academic_standing": academic_standing,
                "updated_at": datetime.now()
            }
        },
        upsert=True
    )
    
    return {
        "student_id": student_id,
        "semester_id": semester_id,
        "weighted_average": weighted_average,
        "gpa": gpa,
        "academic_standing": academic_standing
    }

def get_student_progress(student_id: int) -> Dict[str, Any]:
    """Get comprehensive student progress report"""
    db = get_db()
    
    # Get student info
    student = db.students.find_one({"id": student_id})
    if not student:
        return None
    
    # Get all semesters
    semesters = list(db.semesters.find().sort("school_year", ASCENDING))
    
    # Get all grades
    grades = list(db.grades.find({"student_id": student_id}).sort("semester_id", ASCENDING))
    
    # Get all GPAs
    gpas = list(db.student_gpas.find({"student_id": student_id}).sort("semester_id", ASCENDING))
    
    # Calculate overall statistics
    total_units = sum(gpa.get('total_units', 0) for gpa in gpas)
    overall_gpa = sum(gpa['gpa'] for gpa in gpas) / len(gpas) if gpas else 0
    
    return {
        "student": student,
        "semesters": semesters,
        "grades": grades,
        "gpas": gpas,
        "total_units": total_units,
        "overall_gpa": overall_gpa,
        "current_standing": gpas[-1]['academic_standing'] if gpas else None
    } 