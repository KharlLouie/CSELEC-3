from flask import jsonify, request
from db.mongodb import get_db
from . import subject_bp

@subject_bp.route('/analytics', methods=['GET'])
def get_subject_analytics():
    db = get_db

    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        year = request.args.get('year')
        semester_id = request.args.get('year')
        year = request.args.get('year')
        search_term = request.args.get('search', '').strip()