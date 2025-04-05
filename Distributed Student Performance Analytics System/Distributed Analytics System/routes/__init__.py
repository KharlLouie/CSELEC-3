from .students import student_bp

def init_routes(app):
    print("Initializing routes...")  # Debug line
    
    from .students import student_bp
    app.register_blueprint(student_bp, url_prefix='/students')
    
    # Print all registered routes
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule}")