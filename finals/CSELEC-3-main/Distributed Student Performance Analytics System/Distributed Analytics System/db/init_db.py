from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from schema import COLLECTIONS, INDEXES

# Load environment variables
load_dotenv()

def init_database():
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
    db = client[os.getenv('MONGO_DBNAME', 'CSELEC3DB')]
    
    try:
        # Create collections with validators
        for collection_name, schema in COLLECTIONS.items():
            # Drop existing collection if it exists
            if collection_name in db.list_collection_names():
                db[collection_name].drop()
            
            # Create collection with schema validation
            db.create_collection(
                collection_name,
                validator=schema['validator']
            )
            print(f"✅ Created collection: {collection_name}")
        
        # Create indexes
        for collection_name, indexes in INDEXES.items():
            for index in indexes:
                db[collection_name].create_index(
                    index['keys'],
                    **index.get('options', {})
                )
            print(f"✅ Created indexes for: {collection_name}")
        
        # Create initial semester if none exists
        if db.semesters.count_documents({}) == 0:
            current_year = datetime.now().year
            db.semesters.insert_many([
                {
                    "id": 1,
                    "semester": "First",
                    "school_year": current_year,
                    "status": "active",
                    "start_date": datetime(current_year, 8, 1),
                    "end_date": datetime(current_year, 12, 15),
                    "enrollment_period": {
                        "start": datetime(current_year, 7, 1),
                        "end": datetime(current_year, 7, 31)
                    },
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": 2,
                    "semester": "Second",
                    "school_year": current_year,
                    "status": "upcoming",
                    "start_date": datetime(current_year + 1, 1, 15),
                    "end_date": datetime(current_year + 1, 5, 31),
                    "enrollment_period": {
                        "start": datetime(current_year, 12, 1),
                        "end": datetime(current_year, 12, 31)
                    },
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ])
            print("✅ Created initial semesters")
        
        print("✅ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database() 