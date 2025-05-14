from flask import Blueprint

# Create the blueprint WITHOUT url_prefix here
student_bp = Blueprint('student_bp', __name__)

# Import routes after blueprint creation
from . import performance, subjects, at_risk