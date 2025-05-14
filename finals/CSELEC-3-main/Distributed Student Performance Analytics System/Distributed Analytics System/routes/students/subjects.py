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
        
        # Optimized pipeline to get all required data in a single query
        pipeline = [
            {"$match": {"StudentID": student_id}},
            {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
            {"$unwind": {"path": "$Grades", "includeArrayIndex": "gidx"}},
            {"$match": {"$expr": {"$eq": ["$idx", "$gidx"]}}},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCodes",
                "foreignField": "_id",
                "as": "subject"
            }},
            {"$unwind": "$subject"},
            {"$group": {
                "_id": "$SubjectCodes",
                "student_grade": {"$avg": "$Grades"},
                "description": {"$first": "$subject.Description"},
                "units": {"$first": "$subject.Units"}
            }},
            {"$lookup": {
                "from": "class_averages",
                "let": {"subject_code": "$_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$subject_code", "$$subject_code"]}
                    }},
                    {"$group": {
                        "_id": None,
                        "class_avg": {"$avg": "$average_grade"}
                    }}
                ],
                "as": "class_avg_data"
            }},
            {"$project": {
                "subject_code": "$_id",
                "description": 1,
                "units": 1,
                "student_grade": {"$round": ["$student_grade", 2]},
                "class_avg": {
                    "$round": [
                        {"$ifNull": [
                            {"$arrayElemAt": ["$class_avg_data.class_avg", 0]},
                            0
                        ]},
                        2
                    ]
                },
                "difference": {
                    "$round": [
                        {"$subtract": [
                            "$student_grade",
                            {"$ifNull": [
                                {"$arrayElemAt": ["$class_avg_data.class_avg", 0]},
                                0
                            ]}
                        ]},
                        2
                    ]
                }
            }}
        ]
        
        results = list(db.grades.aggregate(pipeline))
        return format_response(data=results)
        
    except Exception as e:
        return format_response(error=str(e), status_code=500)