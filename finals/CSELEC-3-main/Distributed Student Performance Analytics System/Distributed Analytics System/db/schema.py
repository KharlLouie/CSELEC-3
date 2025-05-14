from datetime import datetime
from bson import ObjectId

# Schema definitions with validation rules
COLLECTIONS = {
    "students": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["id", "name", "course", "status", "enrollment_date"],
                "properties": {
                    "id": {"bsonType": "int"},
                    "name": {"bsonType": "string", "minLength": 1},
                    "course": {"bsonType": "string", "minLength": 1},
                    "status": {"enum": ["active", "inactive", "graduated", "on_leave"]},
                    "enrollment_date": {"bsonType": "date"},
                    "email": {"bsonType": "string", "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
                    "contact_number": {"bsonType": "string"},
                    "year_level": {"bsonType": "int", "minimum": 1, "maximum": 5},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "subjects": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["id", "description", "units", "status"],
                "properties": {
                    "id": {"bsonType": "string"},
                    "description": {"bsonType": "string", "minLength": 1},
                    "units": {"bsonType": "int", "minimum": 1, "maximum": 6},
                    "status": {"enum": ["active", "inactive"]},
                    "prerequisites": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "course_offering": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "semesters": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["id", "semester", "school_year", "status", "start_date", "end_date"],
                "properties": {
                    "id": {"bsonType": "int"},
                    "semester": {"enum": ["First", "Second", "Summer"]},
                    "school_year": {"bsonType": "int", "minimum": 2000},
                    "status": {"enum": ["active", "completed", "upcoming"]},
                    "start_date": {"bsonType": "date"},
                    "end_date": {"bsonType": "date"},
                    "enrollment_period": {
                        "bsonType": "object",
                        "properties": {
                            "start": {"bsonType": "date"},
                            "end": {"bsonType": "date"}
                        }
                    },
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "grades": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["id", "student_id", "subject_codes", "grades", "semester_id", "status"],
                "properties": {
                    "id": {"bsonType": "int"},
                    "student_id": {"bsonType": "int"},
                    "subject_codes": {
                        "bsonType": "array",
                        "items": {"bsonType": "string"},
                        "minItems": 1
                    },
                    "grades": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "int",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "minItems": 1
                    },
                    "semester_id": {"bsonType": "int"},
                    "status": {"enum": ["pending", "finalized", "appealed"]},
                    "remarks": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "last_modified_by": {"bsonType": "string"}
                }
            }
        }
    },
    "class_averages": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["_id", "average_grade", "semester_id", "subject_code", "subject_description", 
                           "passing_rate", "at_risk_rate", "top_grade", "grade_distribution"],
                "properties": {
                    "_id": {"bsonType": "object"},
                    "average_grade": {"bsonType": "double", "minimum": 0, "maximum": 100},
                    "semester_id": {"bsonType": "int"},
                    "subject_code": {"bsonType": "string"},
                    "subject_description": {"bsonType": "string"},
                    "passing_rate": {"bsonType": "double", "minimum": 0, "maximum": 100},
                    "at_risk_rate": {"bsonType": "double", "minimum": 0, "maximum": 100},
                    "top_grade": {"bsonType": "int", "minimum": 0, "maximum": 100},
                    "grade_distribution": {
                        "bsonType": "object",
                        "properties": {
                            "A": {"bsonType": "int", "minimum": 0},
                            "B": {"bsonType": "int", "minimum": 0},
                            "C": {"bsonType": "int", "minimum": 0},
                            "D": {"bsonType": "int", "minimum": 0},
                            "F": {"bsonType": "int", "minimum": 0}
                        }
                    },
                    "total_students": {"bsonType": "int", "minimum": 0},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "student_averages": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["_id", "weighted_average", "student_id", "semester_id"],
                "properties": {
                    "_id": {"bsonType": "int"},
                    "weighted_average": {"bsonType": "double", "minimum": 0, "maximum": 100},
                    "student_id": {"bsonType": "int"},
                    "semester_id": {"bsonType": "int"},
                    "total_units": {"bsonType": "int", "minimum": 0},
                    "subjects_taken": {"bsonType": "int", "minimum": 0},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "student_gpas": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["_id", "weighted_average", "gpa", "student_id", "semester_id"],
                "properties": {
                    "_id": {"bsonType": "int"},
                    "weighted_average": {"bsonType": "double", "minimum": 0, "maximum": 100},
                    "gpa": {"bsonType": "double", "minimum": 0, "maximum": 4.0},
                    "student_id": {"bsonType": "int"},
                    "semester_id": {"bsonType": "int"},
                    "academic_standing": {"enum": ["good", "warning", "probation", "dismissed"]},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"}
                }
            }
        }
    },
    "request_logs": {
        "validator": {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["timestamp", "ip_address", "method", "path", "status_code", "duration_ms"],
                "properties": {
                    "timestamp": {"bsonType": "date"},
                    "ip_address": {"bsonType": "string"},
                    "method": {"bsonType": "string"},
                    "endpoint": {"bsonType": ["string", "null"]},
                    "path": {"bsonType": "string"},
                    "status_code": {"bsonType": "int"},
                    "duration_ms": {"bsonType": "double"},
                    "user_agent": {"bsonType": "string"},
                    "query_params": {"bsonType": "object"},
                    "response_size": {"bsonType": "int"}
                }
            }
        }
    }
}

# Index definitions
INDEXES = {
    "students": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("name", 1)]},
        {"keys": [("course", 1)]},
        {"keys": [("status", 1)]}
    ],
    "subjects": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("description", 1)]},
        {"keys": [("status", 1)]}
    ],
    "semesters": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("school_year", 1), ("semester", 1)], "options": {"unique": True}},
        {"keys": [("status", 1)]}
    ],
    "grades": [
        {"keys": [("id", 1)], "options": {"unique": True}},
        {"keys": [("student_id", 1), ("semester_id", 1)]},
        {"keys": [("semester_id", 1), ("subject_codes", 1)]},
        {"keys": [("status", 1)]}
    ],
    "class_averages": [
        {"keys": [("subject_code", 1), ("semester_id", 1)], "options": {"unique": True}},
        {"keys": [("semester_id", 1)]}
    ],
    "student_averages": [
        {"keys": [("student_id", 1), ("semester_id", 1)], "options": {"unique": True}},
        {"keys": [("semester_id", 1)]}
    ],
    "student_gpas": [
        {"keys": [("student_id", 1), ("semester_id", 1)], "options": {"unique": True}},
        {"keys": [("semester_id", 1)]},
        {"keys": [("academic_standing", 1)]}
    ],
    "request_logs": [
        {"keys": [("timestamp", -1)]},  # For time-based queries
        {"keys": [("ip_address", 1)]},  # For IP-based queries
        {"keys": [("path", 1)]},        # For endpoint-based queries
        {"keys": [("status_code", 1)]}, # For status code analysis
        {"keys": [("duration_ms", 1)]}  # For performance analysis
    ]
} 