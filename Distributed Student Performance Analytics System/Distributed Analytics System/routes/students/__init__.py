from flask import Blueprint

# This creates the blueprint
student_bp = Blueprint('student_bp', __name__)  # Changed name for clarity

# These imports MUST come after blueprint creation
from . import performance, subjects, at_risk