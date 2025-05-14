from pymongo import MongoClient
from flask import current_app

class MongoDB:
    _instance = None

    def __init__(self):
        if not current_app.config['TESTING']:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['CSELEC3DB']

    @classmethod
    def get_db(cls):
        if cls._instance is None:
            cls._instance = MongoDB()
        return cls._instance.db

# Shortcut for routes
get_db = MongoDB.get_db