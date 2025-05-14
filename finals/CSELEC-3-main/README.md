# Distributed Student Performance Analytics System

A Flask-based REST API for tracking and analyzing student performance in educational institutions.

## Features

- Student performance tracking
- Grade management
- GPA calculation
- Academic standing monitoring
- Class performance analytics
- At-risk student identification
- Semester-based analysis

## Tech Stack

- Python 3.8+
- Flask
- MongoDB
- Flask-CORS
- Flask-Caching

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd CSELEC-3-main
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
MONGO_URI=mongodb://localhost:27017/
MONGO_DBNAME=CSELEC3DB
SECRET_KEY=your-secret-key
```

5. Initialize the database:
```bash
python Distributed\ Analytics\ System/db/init_db.py
```

6. Run the application:
```bash
python Distributed\ Analytics\ System/app.py
```

## API Endpoints

### Students
- `GET /students/at_risk` - Get at-risk students
- `GET /students/progress/<student_id>` - Get student progress report

### Subjects
- `GET /subjects` - List all subjects
- `GET /subjects/<subject_id>` - Get subject details

### Analytics
- `GET /home/class-averages` - Get class performance averages
- `GET /home/student-gpas` - Get student GPA reports

## Database Schema

The system uses MongoDB with the following collections:
- students
- subjects
- semesters
- grades
- class_averages
- student_averages
- student_gpas

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 