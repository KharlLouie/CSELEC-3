from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
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
    'CACHE_TYPE': 'SimpleCache',   # In-memory cache
    'CACHE_DEFAULT_TIMEOUT': 300   # Cache timeout: 5 minutes
})

# Initialize shared cache
from cache_config import cache
cache.init_app(app)

# Initialize MongoDB
try:
    client = MongoClient(app.config['MONGO_URI'])
    db = client[app.config['MONGO_DBNAME']]
    print("✅ MongoDB Connected Successfully!")
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")

# Cached test route
@app.route('/test-mongo')
@cache.cached()
def test_mongo():
    try:
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

@app.route('/')
def home():
    return "Student Analytics API - Use /test-mongo to check database"

# Import and register blueprints
from routes.students import student_bp
app.register_blueprint(student_bp, url_prefix='/students')

from routes.subjects import subject_bp
app.register_blueprint(subject_bp, url_prefix='/subjects')

from routes.sy_comprep import genrep_bp
app.register_blueprint(genrep_bp, url_prefix='/home')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
