from flask import Blueprint, request, jsonify
from db.mongodb import get_db
from cache_config import cache

genrep_bp = Blueprint('genrep_bp', __name__)

@genrep_bp.route('/', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def school_year_summary():
    db = get_db()
    selected_sy = request.args.get('sy', type=int)

    try:
        # Get all school years and semesters in a single optimized query
        semesters = list(db.semesters.find(
            {},
            {"_id": 1, "Semester": 1, "SchoolYear": 1}
        ).sort([("SchoolYear", 1), ("Semester", 1)]))
        
        all_school_years = sorted(set(s['SchoolYear'] for s in semesters))

        # If no school year selected, just return dropdown list
        if not selected_sy:
            return jsonify({"school_years": all_school_years})

        # Get selected semesters and their metrics in a single optimized query
        selected_semester_ids = [s['_id'] for s in semesters if s['SchoolYear'] == selected_sy]
        
        if not selected_semester_ids:
            return jsonify({"error": "No semesters found for that school year.", "school_years": all_school_years}), 404

        # Get all metrics for selected semesters in one query
        metrics_data = {
            m['semester_id']: m 
            for m in db.semester_metrics.find(
                {"semester_id": {"$in": selected_semester_ids}},
                {"_id": 0, "semester_id": 1, "average_grade": 1, "passing_rate": 1, "top_grade": 1, "at_risk_rate": 1}
            )
        }

        semester_metrics_list = []
        for sem in semesters:
            if sem['SchoolYear'] == selected_sy:
                metrics = metrics_data.get(sem['_id'], {})
                semester_metrics_list.append({
                    "semester_name": sem['Semester'],
                    "average_grade": metrics.get('average_grade'),
                    "passing_rate": metrics.get('passing_rate'),
                    "top_grade": metrics.get('top_grade'),
                    "at_risk_rate": metrics.get('at_risk_rate')
                })

        # Calculate changes if we have exactly 2 semesters
        changes = {}
        if len(semester_metrics_list) == 2:
            first = semester_metrics_list[0]
            second = semester_metrics_list[1]

            def calc_change(first_val, second_val):
                if first_val is not None and second_val is not None:
                    return round(first_val - second_val, 2)
                return None

            changes = {
                "average_grade_change": calc_change(first['average_grade'], second['average_grade']),
                "passing_rate_change": calc_change(first['passing_rate'], second['passing_rate']),
                "top_grade_change": calc_change(first['top_grade'], second['top_grade']),
                "at_risk_rate_change": calc_change(first['at_risk_rate'], second['at_risk_rate']),
            }

        response = {
            "school_year": selected_sy,
            "school_years": all_school_years,
            "semesters": semester_metrics_list,
            "changes": changes
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
