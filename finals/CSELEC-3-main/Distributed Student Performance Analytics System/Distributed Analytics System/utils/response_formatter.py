from flask import jsonify
from datetime import datetime

def format_response(data=None, error=None, status_code=200):
    response = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success" if not error else "error"
    }
    
    if data:
        response["data"] = data
    if error:
        response["error"] = error
        
    return jsonify(response), status_code