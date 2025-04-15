from flask import Blueprint

# This creates the blueprint
subject_bp = Blueprint('subjects_bp', __name__)  # Changed name for clarity

# These imports MUST come after blueprint creation
from . import analytics