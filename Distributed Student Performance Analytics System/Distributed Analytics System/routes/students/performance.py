from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average

from . import student_bp

@student_bp.route('/performance/<int:student_id>')
def get_performance(student_id):
    db = get_db()

    try:
        # Get student info
        student = db.students.find_one({"_id": student_id})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Get all semesters for dropdown
        semesters = list(db.grades.aggregate([
            {"$match": {"StudentID": student_id}},
            {"$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "semester_info"
            }},
            {"$unwind": "$semester_info"},
            {"$project": {
                "semester_id": "$SemesterID",
                "name": "$semester_info.Semester",
                "year": "$semester_info.SchoolYear"
            }}
        ]))

        if not semesters:
            return jsonify({"error": "No semester data found"}), 404

        # Get semester_id from query params (if any)
        semester_id = request.args.get('semester_id', type=int)
        if semester_id is None:
            semester_id = semesters[0]["semester_id"]

        # Get performance data for the specified semester
        semester_data = list(db.grades.aggregate([
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
        ]))

        if not semester_data or not semester_data[0].get('subjects'):
            return jsonify({"error": "No subject data found for that semester"}), 404

        subjects = semester_data[0]['subjects']
        grades = [s['grade'] for s in subjects]
        Units = [s['Units'] for s in subjects]

        # Calculate overall GPA (from all semesters)
        all_grades = list(db.grades.aggregate([
            {"$match": {"StudentID": student_id}},
            {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx"}},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCodes",
                "foreignField": "_id",
                "as": "subjects"
            }},
            {"$project": {
                "grade": "$Grades",
                "Units": {
                    "$arrayElemAt": [
                        "$subjects.Units",
                        {"$indexOfArray": ["$subjects._id", {"$arrayElemAt": ["$SubjectCodes", "$idx"]}]}
                    ]
                }
            }}
        ]))

        overall_gpa = convert_grade_to_gpa(
            calculate_weighted_average(
                [g['grade'] for g in all_grades],
                [g['Units'] for g in all_grades]
            )
        ) if all_grades else 0.0

        weighted_average = round(calculate_weighted_average(grades, Units), 2)

        return jsonify({
            "student_id": student["_id"],
            "name": student["Name"],
            "course": student["Course"],
            "semesters": semesters,
            "performance": {
                "semester_id": semester_id,
                "overall_gpa": round(overall_gpa, 2),
                "semester_gpa": round(convert_grade_to_gpa(weighted_average), 2),
                "weighted_average": weighted_average,
                "subjects": subjects
            }
        })

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
