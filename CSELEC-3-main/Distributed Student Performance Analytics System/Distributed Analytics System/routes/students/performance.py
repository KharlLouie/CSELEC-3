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
        student = db.students.find_one({"_id": student_id})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        semesters = fetch_all_semesters()
        if not semesters:
            return jsonify({"error": "No semester data found"}), 404

        semester_id = request.args.get("semester_id", default=semesters[0]["id"], type=int)

        semester_data = list(db.grades.aggregate([
            {"$match": {"StudentID": student_id, "SemesterID": semester_id}},
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

        if not semester_data or not semester_data[0].get("subjects"):
            return jsonify({"error": "No subject data found"}), 404

        subjects = semester_data[0]["subjects"]
        grades = [s["grade"] for s in subjects]
        Units = [s["Units"] for s in subjects]

        all_grades = list(db.grades.aggregate([
            {"$match": {"StudentID": student_id}},
            {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
            {"$unwind": {"path": "$Grades", "includeArrayIndex": "gidx"}},
            {"$match": {"$expr": {"$eq": ["$idx", "$gidx"]}}},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCodes",
                "foreignField": "_id",
                "as": "subject_data"
            }},
            {"$unwind": "$subject_data"},
            {"$project": {
                "grade": "$Grades",
                "Units": "$subject_data.Units"
            }}
        ]))

        overall_gpa = convert_grade_to_gpa(
            calculate_weighted_average(
                [g["grade"] for g in all_grades],
                [g["Units"] for g in all_grades]
            )
        ) if all_grades else 0.0

        weighted_average = round(calculate_weighted_average(grades, Units), 2)

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

        students_cursor = db.students.find({}, {"_id": 1, "Name": 1}).skip(skip).limit(limit)
        students = list(students_cursor)

        results = []

        for student in students:
            student_id = student["_id"]

            # Fetch precomputed GPA and weighted average from student_gpas collection
            gpa_entry = db.student_gpas.find_one({"student_id": student_id})
            if not gpa_entry:
                continue  # Skip if no GPA data found

            results.append({
                "student_id": student_id,
                "name": student["Name"],
                "overall_gpa": round(gpa_entry.get("gpa", 0.0), 2),
                "weighted_average": round(gpa_entry.get("weighted_average", 0.0), 2)
            })

        return jsonify({
            "page": page,
            "limit": limit,
            "students": results
        })

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
