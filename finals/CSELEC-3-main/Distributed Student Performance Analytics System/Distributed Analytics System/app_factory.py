from flask import Flask, request, g, current_app
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import time
from datetime import datetime
from db.mongodb import get_db, MongoDB
import sys
import hashlib
from functools import lru_cache

# Load environment variables
load_dotenv()

# Cache for request deduplication (5-minute window)
@lru_cache(maxsize=1000)
def get_request_hash(method, path, query_string, ip_address, timestamp):
    """Generate a unique hash for a request to prevent duplicates"""
    # Round timestamp to nearest minute to group requests within the same minute
    rounded_time = timestamp.replace(second=0, microsecond=0)
    data = f"{method}:{path}:{query_string}:{ip_address}:{rounded_time}"
    return hashlib.md5(data.encode()).hexdigest()

def should_log_request(path):
    """Determine if a request should be logged"""
    # List of paths to exclude from logging
    excluded_paths = {
        '/favicon.ico',
        '/static/',
        '/robots.txt',
        '/health',
        '/metrics'
    }
    
    # List of paths to include (API endpoints)
    included_paths = {
        '/students/',
        '/subjects/',
        '/home/',
        '/test-mongo'
    }
    
    # Check if path should be excluded
    if any(path.startswith(excluded) for excluded in excluded_paths):
        return False
        
    # Check if path should be included
    if any(path.startswith(included) for included in included_paths):
        return True
        
    # Default to not logging unknown paths
    return False

def create_app():
    # Initialize Flask
    app = Flask(__name__)
    CORS(app)

    # Configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'secret_key'),
        'MONGO_URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
        'MONGO_DBNAME': os.getenv('MONGO_DBNAME', 'CSELEC3DB'),
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 300
    })

    # Initialize shared cache
    from cache_config import cache
    cache.init_app(app)

    # Register database teardown
    from db.mongodb import MongoDB
    app.teardown_appcontext(MongoDB.close_db)

    # Initialize MongoDB within app context
    with app.app_context():
        try:
            db = MongoDB.get_db()
            if 'request_logs' not in db.list_collection_names():
                db.create_collection('request_logs')
                db.request_logs.create_index([('timestamp', -1)])
                db.request_logs.create_index([('path', 1)])
                db.request_logs.create_index([('status_code', 1)])
                # Add compound index for request deduplication
                db.request_logs.create_index([
                    ('request_hash', 1),
                    ('timestamp', -1)
                ])
        except Exception as e:
            print(f"MongoDB Connection Failed: {e}")

    # Request logging middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        try:
            # Skip logging for non-API requests
            if not should_log_request(request.path):
                return response

            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Generate request hash for deduplication
            timestamp = datetime.utcnow()
            request_hash = get_request_hash(
                request.method,
                request.path,
                str(sorted(request.args.items())),  # Sort query params for consistency
                request.remote_addr,
                timestamp
            )
            
            # Log request details
            log_entry = {
                'timestamp': timestamp,
                'ip_address': request.remote_addr,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user_agent': request.headers.get('User-Agent', ''),
                'query_params': dict(request.args),
                'response_size': len(response.get_data()),
                'request_hash': request_hash
            }
            
            # Check for duplicate request in the last minute
            try:
                with app.app_context():
                    db = MongoDB.get_db()
                    # Look for duplicate request in the last minute
                    duplicate = db.request_logs.find_one({
                        'request_hash': request_hash,
                        'timestamp': {
                            '$gte': timestamp.replace(second=0, microsecond=0),
                            '$lt': timestamp.replace(second=59, microsecond=999999)
                        }
                    })
                    
                    if not duplicate:
                        # Only log if no duplicate found
                        db.request_logs.insert_one(log_entry)
                        # Simple console log in Flask's default format
                        print(f"[{log_entry['method']}] {log_entry['path']} - {log_entry['status_code']} ({log_entry['duration_ms']}ms)")
            except Exception as e:
                print(f"Failed to log to MongoDB: {e}")
            
            # Add ping time to response headers
            response.headers['X-Response-Time'] = f"{duration * 1000:.2f}ms"
            return response
        except Exception as e:
            print(f"Error in logging: {e}")
            return response

    # Import and register blueprints
    from routes.students import student_bp
    app.register_blueprint(student_bp, url_prefix='/students')

    from routes.subjects import subject_bp
    app.register_blueprint(subject_bp, url_prefix='/subjects')

    from routes.sy_comprep import genrep_bp
    app.register_blueprint(genrep_bp, url_prefix='/home')

    from routes.students.modify import modify_bp
    app.register_blueprint(modify_bp, url_prefix='/students/modify')

    # Register routes
    @app.route('/test-mongo')
    @cache.cached()
    def test_mongo():
        try:
            with app.app_context():
                db = get_db()
                student_count = db.students.count_documents({})
                log_count = db.request_logs.count_documents({})
                return {
                    "status": "success",
                    "student_count": student_count,
                    "log_count": log_count,
                    "collections": db.list_collection_names()
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }, 500

    @app.route('/')
    def home():
        return "Student Analytics API - Use /test-mongo to check database"

    return app