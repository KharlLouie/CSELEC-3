

def init_routes(app):
    print("Initializing routes...")  # Debug line
    
    from .students import student_bp
    app.register_blueprint(student_bp, url_prefix='/students')

    from .subjects import subject_bp
    app.register_blueprint(subject_bp, url_prefix='/subjects')
    
    # Print all registered routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule}")