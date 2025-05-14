from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from cache_config import cache
from . import subject_bp

@subject_bp.route('/analytics', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_subject_analytics():
    db = get_db()

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        year = request.args.get('year', type=int)
        semester_id = request.args.get('semester_id', type=int)

        skip = (page - 1) * per_page
        match_filter = {}

        # Optimize semester filtering
        if semester_id:
            match_filter['semester_id'] = semester_id
        elif year:
            # Get semester IDs for the year in a single query
            semester_ids = [s["_id"] for s in db.semesters.find(
                {"SchoolYear": year},
                {"_id": 1}
            )]
            if semester_ids:
                match_filter['semester_id'] = {"$in": semester_ids}
            else:
                return jsonify({
                    "page": page,
                    "per_page": per_page,
                    "total_subjects": 0,
                    "subjects": [],
                    "semesters": []
                })

        # Optimized pipeline for subject analytics
        pipeline = [
            {"$match": match_filter},
            {"$lookup": {
                "from": "subjects",
                "localField": "subject_code",
                "foreignField": "_id",
                "as": "subject_info"
            }},
            {"$unwind": "$subject_info"},
            {"$project": {
                "_id": 0,
                "subject_code": 1,
                "subject_description": "$subject_info.Description",
                "semester_id": 1,
                "average_grade": {"$round": ["$average_grade", 2]},
                "passing_rate": {"$round": ["$passing_rate", 2]},
                "at_risk_rate": {"$round": ["$at_risk_rate", 2]},
                "top_grade": 1
            }},
            {"$sort": {"subject_code": 1}},
            {"$skip": skip},
            {"$limit": per_page}
        ]

        # Get total count and results in parallel
        total_subjects = db.class_averages.count_documents(match_filter)
        analytics_data = list(db.class_averages.aggregate(pipeline))

        # Get semester options in a single optimized query
        semesters_dropdown = list(db.semesters.find(
            {},
            {"_id": 1, "Semester": 1, "SchoolYear": 1}
        ).sort([("SchoolYear", -1), ("Semester", 1)]))

        formatted_semesters = [
            {
                "id": s["_id"],
                "label": f"{s['Semester']} {s['SchoolYear']}"
            }
            for s in semesters_dropdown
        ]

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_subjects": total_subjects,
            "subjects": analytics_data,
            "semesters": formatted_semesters
        })

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500