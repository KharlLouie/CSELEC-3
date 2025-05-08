from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average
from utils.semesters import fetch_all_semesters
from cache_config import cache

from . import student_bp

@student_bp.route('/performance/<int:student_id>')
@cache.cached(timeout=300, query_string=True)
def get_performance(student_id):
    db = get_db()

    try:
        # Get student and semester data in parallel
        student = db.students.find_one({"_id": student_id}, {"_id": 1, "Name": 1, "Course": 1})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        semesters = fetch_all_semesters()
        if not semesters:
            return jsonify({"error": "No semester data found"}), 404

        semester_id = request.args.get("semester_id", default=semesters[0]["id"], type=int)

        # Optimized pipeline to get all required data in a single query
        pipeline = [
            {"$match": {"StudentID": student_id}},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCodes",
                "foreignField": "_id",
                "as": "subjects"
            }},
            {"$project": {
                "semester_id": "$SemesterID",
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
            }},
            {"$match": {"semester_id": semester_id}}
        ]

        semester_data = list(db.grades.aggregate(pipeline))

        if not semester_data or not semester_data[0].get("subjects"):
            return jsonify({"error": "No subject data found"}), 404

        subjects = semester_data[0]["subjects"]
        grades = [s["grade"] for s in subjects]
        Units = [s["Units"] for s in subjects]

        # Get overall GPA from precomputed collection
        gpa_entry = db.student_gpas.find_one({"student_id": student_id})
        overall_gpa = round(gpa_entry.get("gpa", 0.0), 2) if gpa_entry else 0.0

        weighted_average = round(calculate_weighted_average(grades, Units), 2)

        # Get class averages in bulk
        subject_codes = [s["subject_code"] for s in subjects]
        class_averages = {
            ca["subject_code"]: ca["average_grade"]
            for ca in db.class_averages.find(
                {"subject_code": {"$in": subject_codes}, "semester_id": semester_id},
                {"subject_code": 1, "average_grade": 1, "_id": 0}
            )
        }

        for subject in subjects:
            subject["class_average"] = round(class_averages.get(subject["subject_code"], 0.0), 2)

        return jsonify({
            "student_id": student["_id"],
            "name": student["Name"],
            "course": student["Course"],
            "semesters": semesters,
            "performance": {
                "overall_gpa": overall_gpa,
                "semester_gpa": round(convert_grade_to_gpa(weighted_average), 2),
                "weighted_average": weighted_average,
                "subjects": subjects
            }
        })

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@student_bp.route('/performance/all')
@cache.cached(timeout=300, query_string=True)
def get_all_student_performance():
    db = get_db()

    try:
        page = request.args.get("page", default=1, type=int)
        page = max(page, 1)
        limit = 10
        skip = (page - 1) * limit

        # Optimized query to get students with their GPAs in a single operation
        pipeline = [
            {"$lookup": {
                "from": "student_gpas",
                "localField": "_id",
                "foreignField": "student_id",
                "as": "gpa_data"
            }},
            {"$unwind": {"path": "$gpa_data", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "student_id": "$_id",
                "name": "$Name",
                "overall_gpa": {"$round": ["$gpa_data.gpa", 2]},
                "weighted_average": {"$round": ["$gpa_data.weighted_average", 2]}
            }},
            {"$skip": skip},
            {"$limit": limit}
        ]

        results = list(db.students.aggregate(pipeline))

        return jsonify({
            "page": page,
            "limit": limit,
            "students": results
        })

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
