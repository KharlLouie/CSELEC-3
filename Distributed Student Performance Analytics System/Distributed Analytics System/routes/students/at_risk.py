from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from utils.gpa_calculator import convert_grade_to_gpa, calculate_weighted_average
from celery import Celery
from config import Config

# Initialize Celery
celery = Celery(
    __name__,
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND
)

# Blueprint
from . import student_bp

# Celery Task for Processing At-Risk Students
@celery.task
def process_at_risk_students_task(sort_order, page, page_size, semester_id, search):
    db = get_db()

    try:
        skip = (page - 1) * page_size

        # Stage: Unwind subjects and grades
        base_pipeline = [
            {"$unwind": "$Grades"},
            {"$unwind": "$SubjectCodes"},
            {"$project": {
                "StudentID": 1,
                "SemesterID": 1,
                "grade": "$Grades",
                "subject_code": "$SubjectCodes"
            }},
            {"$match": {
                "grade": {"$lt": 80}
            }},
            {"$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }},
            {"$unwind": "$student"},
        ]

        # Optional semester filter
        if semester_id is not None:
            base_pipeline.insert(3, {"$match": {"SemesterID": semester_id}})

        # Optional search filter
        if search:
            base_pipeline.append({
                "$match": {
                    "$or": [
                        {"student.Name": {"$regex": search, "$options": "i"}},
                        {"student.Course": {"$regex": search, "$options": "i"}}
                    ]
                }
            })

        # Count total first (for pagination)
        count_pipeline = base_pipeline + [{"$count": "total"}]
        total_result = list(db.grades.aggregate(count_pipeline))
        total = total_result[0]["total"] if total_result else 0

        # Continue pipeline for actual data
        full_pipeline = base_pipeline + [
            {"$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "semester"
            }},
            {"$unwind": "$semester"},
            {"$lookup": {
                "from": "subjects",
                "localField": "subject_code",
                "foreignField": "_id",
                "as": "subject"
            }},
            {"$unwind": "$subject"},
            {"$project": {
                "_id": 0,
                "student_id": "$student._id",
                "name": "$student.Name",
                "course": "$student.Course",
                "semester_id": "$SemesterID",
                "semester": "$semester.Semester",
                "year": "$semester.SchoolYear",
                "subject_code": "$subject_code",
                "subject_description": "$subject.Description",
                "grade": 1
            }},
            {"$sort": {"semester_id": -1 if sort_order == "desc" else 1}},
            {"$skip": skip},
            {"$limit": page_size}
        ]

        at_risk = list(db.grades.aggregate(full_pipeline))

        return {
            "page": page,
            "page_size": page_size,
            "total_results": total,
            "total_pages": (total + page_size - 1) // page_size,
            "sort": sort_order,
            "semester_id": semester_id,
            "search": search,
            "students": at_risk
        }

    except Exception as e:
        return {"error": "Internal server error", "message": str(e)}

# Route to Trigger Celery Task
@student_bp.route('/all', methods=['POST'])
def all_at_risk_students():
    try:
        # Query parameters
        sort_order = request.json.get("sort", "desc")
        page = int(request.json.get("page", 1))
        page_size = int(request.json.get("page_size", 10))
        semester_id = request.json.get("semester_id", None)
        search = request.json.get("search", "")

        # Dispatch Celery Task
        task = process_at_risk_students_task.delay(sort_order, page, page_size, semester_id, search)

        return jsonify({
            "message": "Task dispatched",
            "task_id": task.id
        }), 202

    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

# Route to Check Task Status
@student_bp.route('/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    task = process_at_risk_students_task.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            "state": task.state,
            "status": "Task is pending..."
        }
    elif task.state == 'SUCCESS':
        response = {
            "state": task.state,
            "result": task.result
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info)  # Error message or progress info
        }

    return jsonify(response)