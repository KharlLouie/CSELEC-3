from flask import Blueprint, jsonify
from db.mongodb import get_db
from utils.response_formatter import format_response
from cache_config import cache

from . import student_bp

@student_bp.route('/subjects/<int:student_id>')
@cache.cached(timeout=300, query_string=True)
def get_subjects(student_id):
    try:
        db = get_db()
        
        # Get all subjects taken by the student
        student_subjects = db.grades.aggregate([
            {"$match": {"StudentID": student_id}},
            {"$unwind": "$SubjectCodes"},
            {"$group": {"_id": None, "subjects": {"$addToSet": "$SubjectCodes"}}}
        ])
        
        if not student_subjects:
            return format_response(error="No subjects found", status_code=404)
            
        # Get performance data
        pipeline = [
            {"$match": {"SubjectCodes": {"$in": student_subjects[0]["subjects"]}}},
            {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
            {"$group": {
                "_id": "$SubjectCodes",
                "class_avg": {"$avg": {"$arrayElemAt": ["$Grades", "$idx"]}},
                "student_grade": {
                    "$avg": {
                        "$cond": [
                            {"$eq": ["$StudentID", student_id]},
                            {"$arrayElemAt": ["$Grades", "$idx"]},
                            None
                        ]
                    }
                }
            }},
            {"$lookup": {
                "from": "subjects",
                "localField": "_id",
                "foreignField": "_id",
                "as": "subject"
            }},
            {"$unwind": "$subject"},
            {"$project": {
                "subject_code": "$_id",
                "description": "$subject.Description",
                "units": "$subject.units",
                "student_grade": 1,
                "class_avg": 1,
                "difference": {"$subtract": ["$student_grade", "$class_avg"]}
            }}
        ]
        
        results = list(db.grades.aggregate(pipeline))
        return format_response(data=results)
        
    except Exception as e:
        return format_response(error=str(e), status_code=500)