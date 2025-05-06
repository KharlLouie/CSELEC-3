from db.mongodb import get_db

# 1. Compute semester-level weighted averages and GPA
semester_pipeline = [
    {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
    {"$unwind": {"path": "$Grades", "includeArrayIndex": "gidx"}},
    {"$match": {"$expr": {"$eq": ["$idx", "$gidx"]}}},
    {"$lookup": {
        "from": "subjects",
        "localField": "SubjectCodes",
        "foreignField": "_id",
        "as": "subject"
    }},
    {"$unwind": "$subject"},
    {"$project": {
        "StudentID": 1, 
        "SemesterID": 1,
        "grade": "$Grades",
        "units": "$subject.Units"
    }},
    {"$group": {
        "_id": {"student_id": "$StudentID", "semester_id": "$SemesterID"},
        "grades": {"$push": "$grade"},
        "units": {"$push": "$units"}
    }},
    {"$project": {
        "student_id": "$_id.student_id",
        "semester_id": "$_id.semester_id",
        "weighted_sum": {
            "$sum": {
                "$map": {
                    "input": {"$range": [0, {"$size": "$grades"}]},
                    "as": "i",
                    "in": {
                        "$multiply": [
                            {"$arrayElemAt": ["$grades", "$$i"]},
                            {"$arrayElemAt": ["$units", "$$i"]}
                        ]
                    }
                }
            }
        },
        "total_units": {"$sum": "$units"}
    }},
    {"$addFields": {
        "weighted_avg": {"$cond": [
            {"$gt": ["$total_units", 0]},
            {"$divide": ["$weighted_sum", "$total_units"]},
            0
        ]}
    }},
    {"$addFields": {
        "semester_gpa": {
            "$switch": {
                "branches": [
                    {"case": {"$gte": ["$weighted_avg", 96]}, "then": 1.00},
                    {"case": {"$gte": ["$weighted_avg", 93]}, "then": 1.25},
                    {"case": {"$gte": ["$weighted_avg", 90]}, "then": 1.50},
                    {"case": {"$gte": ["$weighted_avg", 87]}, "then": 1.75},
                    {"case": {"$gte": ["$weighted_avg", 84]}, "then": 2.00},
                    {"case": {"$gte": ["$weighted_avg", 80]}, "then": 2.25},
                    {"case": {"$gte": ["$weighted_avg", 78]}, "then": 2.50},
                    {"case": {"$gte": ["$weighted_avg", 76]}, "then": 2.75},
                    {"case": {"$eq": ["$weighted_avg", 75]}, "then": 3.00}
                ],
                "default": 5.00
            }
        }
    }},
    {"$project": {
        "_id": 0,
        "student_id": 1,
        "semester_id": 1,
        "semester_gpa": 1,
        "weighted_avg": 1
    }},
    {"$merge": {
        "into": "student_gpas",
        "on": ["student_id", "semester_id"],
        "whenMatched": "merge",
        "whenNotMatched": "insert"
    }}
]

db.grades.aggregate(semester_pipeline)

# 2. Compute overall GPA based on all semester weighted averages
overall_pipeline = [
    {"$group": {
        "_id": "$student_id",
        "avg_weighted": {"$avg": "$weighted_avg"}
    }},
    {"$addFields": {
        "overall_gpa": {
            "$switch": {
                "branches": [
                    {"case": {"$gte": ["$avg_weighted", 96]}, "then": 1.00},
                    {"case": {"$gte": ["$avg_weighted", 93]}, "then": 1.25},
                    {"case": {"$gte": ["$avg_weighted", 90]}, "then": 1.50},
                    {"case": {"$gte": ["$avg_weighted", 87]}, "then": 1.75},
                    {"case": {"$gte": ["$avg_weighted", 84]}, "then": 2.00},
                    {"case": {"$gte": ["$avg_weighted", 80]}, "then": 2.25},
                    {"case": {"$gte": ["$avg_weighted", 78]}, "then": 2.50},
                    {"case": {"$gte": ["$avg_weighted", 76]}, "then": 2.75},
                    {"case": {"$eq": ["$avg_weighted", 75]}, "then": 3.00}
                ],
                "default": 5.00
            }
        }
    }},
    {"$merge": {
        "into": "student_gpas",
        "on": "_id",
        "whenMatched": "merge",
        "whenNotMatched": "discard"
    }}
]

db.student_gpas.aggregate(overall_pipeline)

print("✅ student_gpas collection updated with Philippine GPA scale.")
