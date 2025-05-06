from flask import Blueprint, request, jsonify
from db.mongodb import get_db

genrep_bp = Blueprint('genrep_bp', __name__)

@genrep_bp.route('/', methods=['GET'])
def school_year_summary():
    db = get_db()
    selected_sy = request.args.get('sy', type=int)

    try:
        # Step 1: Get all school years from semesters
        semesters = list(db.semesters.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1}))
        all_school_years = sorted(set(s['SchoolYear'] for s in semesters))

        # If no school year selected, just return dropdown list
        if not selected_sy:
            return jsonify({"school_years": all_school_years})

        # Step 2: Find semesters for selected school year
        selected_semesters = [s for s in semesters if s['SchoolYear'] == selected_sy]

        if not selected_semesters:
            return jsonify({"error": "No semesters found for that school year.", "school_years": all_school_years}), 404

        semester_metrics_list = []

        for sem in selected_semesters:
            # Look up metrics based on semester _id
            metrics = db.semester_metrics.find_one({"semester_id": sem['_id']}, {"_id": 0})
            if metrics:
                semester_metrics_list.append({
                    "semester_name": sem['Semester'],
                    "average_grade": metrics.get('average_grade'),
                    "passing_rate": metrics.get('passing_rate'),
                    "top_grade": metrics.get('top_grade'),
                    "at_risk_rate": metrics.get('at_risk_rate')
                })
            else:
                semester_metrics_list.append({
                    "semester_name": sem['Semester'],
                    "average_grade": None,
                    "passing_rate": None,
                    "top_grade": None,
                    "at_risk_rate": None
                })

        # Step 3: If exactly 2 semesters (ex: FirstSem and SecondSem), compute changes
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
