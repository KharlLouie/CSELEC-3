from flask import Blueprint, jsonify, request, current_app
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average
from utils.semesters import fetch_all_semesters
from cache_config import cache
import multiprocessing as mp
from functools import partial
import copy
from flask import current_app
import traceback
from multiprocessing import Pool, cpu_count
from app_factory import create_app

from . import student_bp

def init_worker():
    """Initialize worker process with Flask app context"""
    global app
    app = create_app()
    app.app_context().push()

def process_subject_data(subject, class_averages, semester_id):
    """Process individual subject data in parallel"""
    try:
        return {
            **subject,
            "class_average": round(class_averages.get(subject["subject_code"], 0.0), 2)
        }
    except Exception as e:
        print(f"Error processing subject data: {str(e)}")
        raise

def process_student_worker(student):
    """Process a single student in a worker process"""
    try:
        db = get_db()
        gpa_entry = db.student_gpas.find_one({"student_id": student["_id"]})
        return {
            "student_id": student["_id"],
            "name": student["Name"],
            "overall_gpa": round(gpa_entry.get("gpa", 0.0), 2) if gpa_entry else 0.0,
            "weighted_average": round(gpa_entry.get("weighted_average", 0.0), 2) if gpa_entry else 0.0
        }
    except Exception as e:
        print(f"Error processing student {student.get('_id')}: {str(e)}")
        return None

def process_subject_worker(subject_data):
    """Process a single subject with its class average"""
    try:
        subject, class_average = subject_data
        return {
            **subject,
            "class_average": round(class_average, 2)
        }
    except Exception as e:
        print(f"Error processing subject {subject.get('subject_code')}: {str(e)}")
        return subject

@student_bp.route('/performance/<int:student_id>')
@cache.cached(timeout=300, query_string=True)
def get_performance(student_id):
    try:
        print(f"Starting processing for student {student_id}...")
        db = get_db()

        # Get semester ID from request or default
        semesters = fetch_all_semesters()
        if not semesters:
            print("No semester data found")
            return jsonify({"error": "No semester data found"}), 404

        semester_id = request.args.get("semester_id", default=semesters[0]["id"], type=int)
        print(f"Processing semester {semester_id}")

        # Get student info (simple query)
        student = db.students.find_one(
            {"_id": student_id},
            {"_id": 1, "Name": 1, "Course": 1}
        )
        if not student:
            print(f"Student {student_id} not found")
            return jsonify({"error": "Student not found"}), 404

        # Get grades data with subjects (single aggregation)
        grades_pipeline = [
            {"$match": {
                "StudentID": student_id,
                "SemesterID": semester_id
            }},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCodes",
                "foreignField": "_id",
                "as": "subjects"
            }},
            {"$project": {
                "subjects": {
                    "$map": {
                        "input": {"$range": [0, {"$size": "$SubjectCodes"}]},
                        "as": "idx",
                        "in": {
                            "subject_code": {"$arrayElemAt": ["$SubjectCodes", "$$idx"]},
                            "grade": {"$arrayElemAt": ["$Grades", "$$idx"]},
                            "description": {
                                "$arrayElemAt": [
                                    "$subjects.Description",
                                    {"$indexOfArray": ["$subjects._id", {"$arrayElemAt": ["$SubjectCodes", "$$idx"]}]}
                                ]
                            },
                            "Units": {
                                "$arrayElemAt": [
                                    "$subjects.Units",
                                    {"$indexOfArray": ["$subjects._id", {"$arrayElemAt": ["$SubjectCodes", "$$idx"]}]}
                                ]
                            }
                        }
                    }
                }
            }}
        ]

        grades_data = list(db.grades.aggregate(grades_pipeline))
        if not grades_data or not grades_data[0].get("subjects"):
            print(f"No subject data found for student {student_id} in semester {semester_id}")
            return jsonify({"error": "No subject data found"}), 404

        subjects = grades_data[0]["subjects"]
        print(f"Found {len(subjects)} subjects")

        # Get class averages in a single query
        subject_codes = [s["subject_code"] for s in subjects]
        class_averages = {
            ca["subject_code"]: ca["average_grade"]
            for ca in db.class_averages.find(
                {"subject_code": {"$in": subject_codes}, "semester_id": semester_id},
                {"subject_code": 1, "average_grade": 1, "_id": 0}
            )
        }

        # Get GPA data (simple query)
        gpa_entry = db.student_gpas.find_one(
            {"student_id": student_id},
            {"gpa": 1, "weighted_average": 1, "_id": 0}
        )

        # Prepare data for parallel processing
        subject_data_list = [
            (subject, class_averages.get(subject["subject_code"], 0.0))
            for subject in subjects
        ]

        # Process subjects in parallel
        num_workers = min(cpu_count(), 4)  # Limit to 4 workers max
        print(f"Using {num_workers} worker processes for subject processing")

        try:
            # Create a pool of workers
            ctx = mp.get_context('spawn')
            with Pool(processes=num_workers, context=ctx) as pool:
                # Process subjects in parallel
                print("Starting parallel subject processing...")
                processed_subjects = []
                for result in pool.imap_unordered(process_subject_worker, subject_data_list, chunksize=2):
                    if result is not None:
                        processed_subjects.append(result)
                print(f"Successfully processed {len(processed_subjects)} subjects")

        except Exception as e:
            print(f"Error in parallel processing: {str(e)}")
            print(traceback.format_exc())
            # Fallback to sequential processing
            processed_subjects = []
            for subject in subjects:
                try:
                    processed_subjects.append({
                        **subject,
                        "class_average": round(class_averages.get(subject["subject_code"], 0.0), 2)
                    })
                except Exception as e:
                    print(f"Error processing subject {subject.get('subject_code')}: {str(e)}")
                    processed_subjects.append(subject)

        # Calculate weighted average
        grades = [s["grade"] for s in subjects]
        units = [s["Units"] for s in subjects]
        weighted_average = round(calculate_weighted_average(grades, units), 2)

        return jsonify({
            "student_id": student_id,
            "name": student["Name"],
            "course": student["Course"],
            "semester_id": semester_id,
            "subjects": processed_subjects,
            "overall_gpa": round(gpa_entry.get("gpa", 0.0), 2) if gpa_entry else 0.0,
            "weighted_average": weighted_average
        })

    except Exception as e:
        print(f"Error in get_performance: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@student_bp.route('/performance/all')
@cache.cached(timeout=300, query_string=True)
def get_all_student_performance():
    db = get_db()

    try:
        print("Starting /all endpoint processing...")
        page = request.args.get("page", default=1, type=int)
        page = max(page, 1)
        limit = 10
        skip = (page - 1) * limit

        # Get total count first
        total_students = db.students.count_documents({})
        print(f"Total students in database: {total_students}")
        
        # Get students in batches
        students = list(db.students.find({}, {"_id": 1, "Name": 1}).skip(skip).limit(limit))
        print(f"Retrieved {len(students)} students for page {page}")
        
        if not students:
            print("No students found for the current page")
            return jsonify({
                "page": page,
                "limit": limit,
                "total_students": total_students,
                "students": []
            })

        # Use multiprocessing Pool
        num_workers = min(cpu_count(), 4)  # Limit to 4 workers max
        print(f"Using {num_workers} worker processes")
        
        try:
            # Create a pool of workers with proper initialization
            ctx = mp.get_context('spawn')  # Use spawn to avoid context issues
            with Pool(processes=num_workers, initializer=init_worker, context=ctx) as pool:
                # Process students in parallel
                print("Starting parallel processing...")
                results = []
                for result in pool.imap_unordered(process_student_worker, students, chunksize=2):
                    if result is not None:
                        results.append(result)
                print(f"Processed {len(results)} students successfully")

        except Exception as e:
            print(f"Error in multiprocessing pool: {str(e)}")
            print(traceback.format_exc())
            # Fallback to sequential processing
            results = []
            for student in students:
                try:
                    gpa_entry = db.student_gpas.find_one({"student_id": student["_id"]})
                    results.append({
                        "student_id": student["_id"],
                        "name": student["Name"],
                        "overall_gpa": round(gpa_entry.get("gpa", 0.0), 2) if gpa_entry else 0.0,
                        "weighted_average": round(gpa_entry.get("weighted_average", 0.0), 2) if gpa_entry else 0.0
                    })
                except Exception as e:
                    print(f"Error processing student {student.get('_id')}: {str(e)}")
                    continue

        print(f"Final results count: {len(results)}")
        return jsonify({
            "page": page,
            "limit": limit,
            "total_students": total_students,
            "students": results
        })

    except Exception as e:
        print(f"Error in get_all_student_performance: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
