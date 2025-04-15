from flask import jsonify, request
from db.mongodb import get_db
from . import student_bp

@student_bp.route('/at_risk', methods=['GET'])
def get_at_risk_students():
    db = get_db()

    try:
        # Parse query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        semester_id = request.args.get('semester_id')
        search_term = request.args.get('search', '').strip()

        # Cap the max limit
        per_page = min(per_page, 100)
        skip = (page - 1) * per_page

        # Base match condition for at-risk students (any grade < 80)
        match_conditions = {
            "Grades": {"$elemMatch": {"$lt": 80}}
        }

        # Filter by semester if provided (cast to int)
        if semester_id:
            match_conditions["SemesterID"] = int(semester_id)

        # MongoDB aggregation pipeline
        pipeline = [
            {"$match": match_conditions},
            {"$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }},
            {"$unwind": "$student"},
            {"$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "semester"
            }},
            {"$unwind": "$semester"},
        ]

        # Add search filter after student data is available
        if search_term:
            pipeline.append({
                "$match": {
                    "$or": [
                        {"student.Name": {"$regex": search_term, "$options": "i"}},
                        {"student.Course": {"$regex": search_term, "$options": "i"}}
                    ]
                }
            })

        # Pagination
        pipeline.extend([
            {"$skip": skip},
            {"$limit": per_page}
        ])

        # Run the pipeline
        results = list(db.grades.aggregate(pipeline))

        return jsonify({
            "success": True,
            "count": len(results),
            "page": page,
            "limit": per_page,
            "data": results
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve at-risk students"
        }), 500