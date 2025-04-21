from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Configuration
app.config.update({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'secret_key'),
    'MONGO_URI': os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
    'MONGO_DBNAME': os.getenv('MONGO_DBNAME', 'CSELEC3DB'),
    'CELERY_BROKER_URL': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    'CELERY_RESULT_BACKEND': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
})

# Initialize MongoDB
try:
    client = MongoClient(app.config['MONGO_URI'])
    db = client[app.config['MONGO_DBNAME']]
    print("✅ MongoDB Connected Successfully!")
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

# Initialize Celery
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

# Example Celery Task
@celery.task
def process_student_data(student_id):
    # Simulate processing a student's data
    print(f"Processing student {student_id}")
    return f"Processed student {student_id}"

# Simple Test Route
@app.route('/test-mongo')
def test_mongo():
    try:
        # Try a simple query
        student_count = db.students.count_documents({})
        return jsonify({
            "status": "success",
            "student_count": student_count,
            "collections": db.list_collection_names()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Route to Trigger Celery Task
@app.route('/process-student/<int:student_id>')
def trigger_celery_task(student_id):
    task = process_student_data.delay(student_id)
    return jsonify({
        "message": "Task dispatched",
        "task_id": task.id
    }), 202

# Import and register blueprints
from routes.students import student_bp
app.register_blueprint(student_bp, url_prefix='/students')
from routes.subjects import subject_bp
app.register_blueprint(subject_bp, url_prefix='/subjects')

@app.route('/')
def home():
    return "Student Analytics API - Use /test-mongo to check database"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)