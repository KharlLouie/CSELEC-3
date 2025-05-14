from pymongo import MongoClient
from flask import current_app, g

class MongoDB:
    _instance = None

    def __init__(self):
        if not current_app.config.get('TESTING', False):
            self.client = MongoClient(current_app.config.get('MONGO_URI', 'mongodb://localhost:27017/'))
            self.db = self.client[current_app.config.get('MONGO_DBNAME', 'CSELEC3DB')]

    @classmethod
    def get_db(cls):
        if 'db' not in g:
            if cls._instance is None:
                cls._instance = MongoDB()
            g.db = cls._instance.db
        return g.db

    @classmethod
    def close_db(cls, e=None):
        db = g.pop('db', None)
        if db is not None and cls._instance is not None:
            cls._instance.client.close()
            cls._instance = None

# Shortcut for routes
get_db = MongoDB.get_db