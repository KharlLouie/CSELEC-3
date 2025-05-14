from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average
from datetime import datetime
from cache_config import cache
from utils.semesters import fetch_all_semesters
from routes.students.performance import get_performance, get_all_student_performance
from utils.class_average_updater import update_class_average_for_subject_semester
from routes.students.at_risk import get_at_risk_students
from routes.students.subjects import get_subjects
from routes.sy_comprep import school_year_summary
from cache_config import clear_all_caches

modify_bp = Blueprint('modify', __name__)

@modify_bp.route('/debug/subjects', methods=['GET'])
def debug_subjects():
    try:
        db = get_db()
        subjects = list(db.subjects.find({}, {'_id': 0}))
        return jsonify({
            "count": len(subjects),
            "subjects": subjects
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@modify_bp.route('/update-grade', methods=['POST'])
def update_grade():
    try:
        data = request.get_json()
        print('=== BACKEND DEBUG LOGS ===')
        print(f"Raw request data: {data}")
        print(f"Request content type: {request.content_type}")
        print(f"Request headers: {dict(request.headers)}")
        print('========================')

        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['student_id', 'subject_code', 'semester_id', 'new_grade']
        for field in required_fields:
            if field not in data:
                print(f"Missing field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400
            print(f"Field {field}: {data[field]} (type: {type(data[field])})")

        student_id = int(data['student_id'])
        subject_code = data['subject_code']
        semester_id = int(data['semester_id'])
        new_grade = int(float(data['new_grade']))

        print(f"Processed values:")
        print(f"student_id: {student_id} (type: {type(student_id)})")
        print(f"subject_code: {subject_code} (type: {type(subject_code)})")
        print(f"semester_id: {semester_id} (type: {type(semester_id)})")
        print(f"new_grade: {new_grade} (type: {type(new_grade)})")
        print('========================')

        # Validate grade range
        if not (0 <= new_grade <= 100):
            return jsonify({"error": "Grade must be between 0 and 100"}), 400

        db = get_db()

        # First, find the student's data
        print('=== STUDENT LOOKUP DEBUG ===')
        print(f"Looking for student with ID: {student_id}")
        student_data = db.students.find_one({"_id": student_id})
        print(f"Found student data: {student_data}")
        print('===========================')

        if not student_data:
            return jsonify({"error": "Student not found"}), 404

        # Get grades data with subjects using aggregation
        print('=== GRADES LOOKUP DEBUG ===')
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
        print(f"Found grades data: {grades_data}")
        
        if not grades_data or not grades_data[0].get("subjects"):
            print(f"No subject data found for student {student_id} in semester {semester_id}")
            return jsonify({"error": "No subject data found"}), 404

        subjects = grades_data[0]["subjects"]
        print(f"Found subjects: {subjects}")
        print('===========================')

        # Find the subject in the subjects list
        subject_info = next(
            (s for s in subjects if s.get('subject_code') == subject_code),
            None
        )

        if not subject_info:
            print(f"Subject {subject_code} not found in subjects")
            return jsonify({"error": f"Subject {subject_code} not found in subjects"}), 404

        print(f"Found subject info: {subject_info}")

        # Find the grades document for this student and semester
        grades_doc = db.grades.find_one({
            "StudentID": student_id,
            "SemesterID": semester_id
        })

        print(f"Found grades document: {grades_doc}")

        if not grades_doc:
            return jsonify({"error": "No grades found for this student and semester"}), 404

        # Find the index of the subject code in the SubjectCodes array
        try:
            print(f"Looking for subject {subject_code} in {grades_doc['SubjectCodes']}")
            subject_index = grades_doc['SubjectCodes'].index(subject_code)
            print(f"Found subject at index {subject_index}")
        except ValueError:
            print(f"Subject {subject_code} not found in grades document")
            return jsonify({"error": f"Subject {subject_code} not found in grades document"}), 404

        # Create a new grades array with the updated grade
        new_grades = grades_doc['Grades'].copy()
        new_grades[subject_index] = new_grade

        # Update the grades document
        result = db.grades.update_one(
            {
                "StudentID": student_id,
                "SemesterID": semester_id
            },
            {
                "$set": {
                    "Grades": new_grades,
                    "updated_at": datetime.now()
                }
            }
        )

        print(f"Update result: {result.modified_count} documents modified")

        if result.modified_count == 0:
            return jsonify({"error": "Failed to update grade"}), 500

        # Calculate weighted average using the subject information from the grades data
        total_units = 0
        total_weighted_grade = 0
        
        # Get all subjects for this student and semester
        for i, grade in enumerate(new_grades):
            subject_code = grades_doc['SubjectCodes'][i]
            # Find the subject in the subjects list
            subject_info = next(
                (s for s in subjects if s.get('subject_code') == subject_code),
                None
            )
            
            if subject_info:
                units = subject_info.get('Units', 3)  # Default to 3 units if not specified
                total_units += units
                total_weighted_grade += grade * units

        weighted_avg = total_weighted_grade / total_units if total_units > 0 else 0
        
        # Update student averages
        db.student_averages.update_one(
            {
                "student_id": student_id
            },
            {
                "$set": {
                    "weighted_average": weighted_avg,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )

        # Calculate new GPA
        gpa = convert_grade_to_gpa(weighted_avg)
        
        # Update student GPA
        db.student_gpas.update_one(
            {
                "student_id": student_id
            },
            {
                "$set": {
                    "weighted_average": weighted_avg,
                    "gpa": gpa,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )

        # Update class averages for the modified subject
        update_class_average_for_subject_semester(subject_code, semester_id)

        # After updating grades, clear all caches
        if not clear_all_caches():
            print("Warning: Cache clearing may have failed")
        
        return jsonify({
            "message": "Grade updated successfully",
            "new_grade": new_grade,
            "weighted_average": weighted_avg,
            "gpa": gpa
        })

    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        return jsonify({"error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500

@modify_bp.route('/batch-update-grades', methods=['POST'])
def batch_update_grades():
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"error": "Expected a list of grade updates"}), 400

        # Validate all updates first
        validated_updates = []
        for update in data:
            if not all(k in update for k in ['student_id', 'subject_code', 'semester_id', 'new_grade']):
                return jsonify({"error": f"Missing required fields in update: {update}"}), 400
            
            try:
                validated_update = {
                    'student_id': int(update['student_id']),
                    'subject_code': str(update['subject_code']),
                    'semester_id': int(update['semester_id']),
                    'new_grade': int(float(update['new_grade']))
                }
                
                if not (0 <= validated_update['new_grade'] <= 100):
                    return jsonify({"error": f"Grade must be between 0 and 100 for update: {update}"}), 400
                    
                validated_updates.append(validated_update)
            except (ValueError, TypeError) as e:
                return jsonify({"error": f"Invalid data format in update: {update}. Error: {str(e)}"}), 400

        db = get_db()
        results = []
        errors = []

        # Group updates by student and semester for efficient processing
        updates_by_student_semester = {}
        for update in validated_updates:
            key = (update['student_id'], update['semester_id'])
            if key not in updates_by_student_semester:
                updates_by_student_semester[key] = []
            updates_by_student_semester[key].append(update)

        # Process each student-semester group
        for (student_id, semester_id), updates in updates_by_student_semester.items():
            try:
                # Get grades document for this student and semester
                grades_doc = db.grades.find_one({
                    "StudentID": student_id,
                    "SemesterID": semester_id
                })

                if not grades_doc:
                    errors.append({
                        "student_id": student_id,
                        "semester_id": semester_id,
                        "error": "No grades found for this student and semester"
                    })
                    continue

                # Create a new grades array with all updates
                new_grades = grades_doc['Grades'].copy()
                subject_updates = {}  # Track which subjects were updated

                for update in updates:
                    try:
                        subject_index = grades_doc['SubjectCodes'].index(update['subject_code'])
                        new_grades[subject_index] = update['new_grade']
                        subject_updates[update['subject_code']] = update['new_grade']
                    except ValueError:
                        errors.append({
                            "student_id": student_id,
                            "subject_code": update['subject_code'],
                            "error": "Subject not found in grades document"
                        })
                        continue

                # Update the grades document
                result = db.grades.update_one(
                    {
                        "StudentID": student_id,
                        "SemesterID": semester_id
                    },
                    {
                        "$set": {
                            "Grades": new_grades,
                            "updated_at": datetime.now()
                        }
                    }
                )

                if result.modified_count > 0:
                    # Get subjects information for weighted average calculation
                    subjects = list(db.subjects.find(
                        {"_id": {"$in": grades_doc['SubjectCodes']}},
                        {"_id": 1, "Units": 1}
                    ))

                    # Calculate weighted average
                    total_units = 0
                    total_weighted_grade = 0
                    for i, grade in enumerate(new_grades):
                        subject = next((s for s in subjects if s['_id'] == grades_doc['SubjectCodes'][i]), None)
                        if subject:
                            units = subject.get('Units', 3)
                            total_units += units
                            total_weighted_grade += grade * units

                    weighted_avg = total_weighted_grade / total_units if total_units > 0 else 0
                    gpa = convert_grade_to_gpa(weighted_avg)

                    # Update student averages and GPA
                    db.student_averages.update_one(
                        {"student_id": student_id},
                        {
                            "$set": {
                                "weighted_average": weighted_avg,
                                "updated_at": datetime.now()
                            }
                        },
                        upsert=True
                    )

                    db.student_gpas.update_one(
                        {"student_id": student_id},
                        {
                            "$set": {
                                "weighted_average": weighted_avg,
                                "gpa": gpa,
                                "updated_at": datetime.now()
                            }
                        },
                        upsert=True
                    )

                    # Update class averages for modified subjects
                    for subject_code in subject_updates:
                        update_class_average_for_subject_semester(subject_code, semester_id)

                    results.append({
                        "student_id": student_id,
                        "semester_id": semester_id,
                        "updated_subjects": list(subject_updates.keys()),
                        "weighted_average": weighted_avg,
                        "gpa": gpa
                    })

            except Exception as e:
                errors.append({
                    "student_id": student_id,
                    "semester_id": semester_id,
                    "error": str(e)
                })

        # Clear all caches after batch update
        if not clear_all_caches():
            print("Warning: Cache clearing may have failed")

        return jsonify({
            "message": "Batch update completed",
            "successful_updates": results,
            "errors": errors
        })

    except Exception as e:
        print(f"Batch update error: {str(e)}")
        return jsonify({"error": str(e)}), 500
