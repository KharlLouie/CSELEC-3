from flask import Blueprint

def init_routes(app):
    print("Initializing routes...")  # Debug line
    
    # Import blueprints
    from .students import student_bp
    from .subjects import subject_bp
    from .sy_comprep import genrep_bp
    
    # Register blueprints with prefixes
    app.register_blueprint(student_bp, url_prefix='/students')
    app.register_blueprint(subject_bp, url_prefix='/subjects')
    app.register_blueprint(genrep_bp, url_prefix='/home')
    
    
    # Debug print all registered routes
    print("\nRegistered routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        methods = ','.join(sorted(rule.methods))
        print(f"{rule.rule:50} {methods:20} {rule.endpoint}")
    
    print("\nRoute initialization complete.")