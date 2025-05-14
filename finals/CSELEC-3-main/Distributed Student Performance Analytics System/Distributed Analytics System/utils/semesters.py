# utils/semesters.py
from db.mongodb import get_db

def fetch_all_semesters():
    db = get_db()
    semesters = list(db.semesters.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1}))
    return [
        {
            "id": sem["_id"],
            "label": f"{sem['Semester']} - SY {sem['SchoolYear']}",
            "Semester": sem["Semester"],
            "SchoolYear": sem["SchoolYear"]
        }
        for sem in semesters
    ]
