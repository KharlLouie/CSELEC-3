from flask import Blueprint, jsonify, request
from db.mongodb import get_db
from . import subject_bp

@subject_bp.route('/analytics', methods=['GET'])
def get_subject_analytics():
    db = get_db()

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        year = request.args.get('year', type=int)
        semester_id = request.args.get('semester_id', type=int)

        skip = (page - 1) * per_page
        match_filter = {}

        # Filter by semester only if semester_id is specified
        if semester_id:
            match_filter['semester_id'] = semester_id

        # Filter by year only if year is specified
        if year:
            matching_semesters = db.semesters.find(
                {"SchoolYear": year},
                {"_id": 1}
            )
            semester_ids = [s["_id"] for s in matching_semesters]
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

        # Pipeline for paginated subject analytics
        pipeline = [
            {"$match": match_filter},
            {"$project": {
                "_id": 0,
                "subject_code": 1,
                "subject_description": 1,
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

        analytics_data = list(db.class_averages.aggregate(pipeline))
        total_subjects = db.class_averages.count_documents(match_filter)

        # Get dropdown options for all semesters
        all_semesters = list(db.semesters.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1}))
        semesters_dropdown = [
            {
                "id": s["_id"],
                "label": f"{s['Semester']} {s['SchoolYear']}"
            }
            for s in all_semesters
        ]

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_subjects": total_subjects,
            "subjects": analytics_data,
            "semesters": semesters_dropdown
        })

    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
