# utils/class_average_updater.py

from db.mongodb import get_db

def update_entire_class_average():
    db = get_db()
    pipeline = [
        {"$unwind": "$Grades"},
        {"$group": {
            "_id": {
                "subject_code": {"$arrayElemAt": ["$SubjectCodes", 0]},
                "semester_id": "$SemesterID"
            },
            "average_grade": {"$avg": "$Grades"}
        }},
        {"$lookup": {
            "from": "subjects",
            "localField": "_id.subject_code",
            "foreignField": "_id",
            "as": "subject_info"
        }},
        {"$unwind": "$subject_info"},
        {"$project": {
            "semester_id": "$_id.semester_id",
            "subject_code": "$_id.subject_code",
            "average_grade": 1,
            "subject_description": "$subject_info.Description"
        }}
    ]

    result = db.grades.aggregate(pipeline)

    for doc in result:
        db.class_averages.update_one(
            {"_id": {"subject_code": doc["subject_code"], "semester_id": doc["semester_id"]}},
            {"$set": {
                "average_grade": doc["average_grade"],
                "subject_description": doc["subject_description"]
            }},
            upsert=True
        )

def update_class_average_for_subject_semester(subject_code, semester_id):
    db = get_db()

    grades_cursor = db.grades.find({
        "SubjectCodes": subject_code,
        "SemesterID": semester_id
    })

    grades = []
    for grade_doc in grades_cursor:
        idx = grade_doc["SubjectCodes"].index(subject_code)
        grades.append(grade_doc["Grades"][idx])

    if not grades:
        return

    avg_grade = sum(grades) / len(grades)

    subject = db.subjects.find_one({"_id": subject_code})
    if not subject:
        return

    db.class_averages.update_one(
        {"_id": {"subject_code": subject_code, "semester_id": semester_id}},
        {"$set": {
            "average_grade": avg_grade,
            "subject_description": subject["Description"]
        }},
        upsert=True
    )
