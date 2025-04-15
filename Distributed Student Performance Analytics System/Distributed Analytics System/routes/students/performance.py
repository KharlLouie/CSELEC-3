from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average
from utils.semesters import fetch_all_semesters  # <- Import the util

from . import student_bp

@student_bp.route('/performance/<int:student_id>')
def get_performance(student_id):
    db = get_db()

    try:
        # Get student info
        student = db.students.find_one({"_id": student_id})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Get all semesters from util
        semesters = fetch_all_semesters()
        if not semesters:
            return jsonify({"error": "No semester data found"}), 404

        semester_id = request.args.get("semester_id", default=semesters[0]["id"], type=int)

        # Get performance for selected semester
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
            return jsonify({"error": "No subject data found"}), 404

        subjects = semester_data[0]['subjects']
        grades = [s['grade'] for s in subjects]
        Units = [s['Units'] for s in subjects]

        # Calculate GPA
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

        # Lookup class averages
        for subject in subjects:
            class_avg = db.class_averages.find_one({
                "subject_code": subject["subject_code"],
                "semester_id": semester_id
            })
            subject["class_average"] = round(class_avg["average_grade"], 2) if class_avg else 0.0

        return jsonify({
            "student_id": student["_id"],
            "name": student["Name"],
            "course": student["Course"],
            "semesters": semesters,
            "performance": {
                "overall_gpa": round(overall_gpa, 2),
                "semester_gpa": round(convert_grade_to_gpa(weighted_average), 2),
                "weighted_average": round(weighted_average, 2),
                "subjects": subjects
            }
        })

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500
