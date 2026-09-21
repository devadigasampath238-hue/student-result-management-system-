"""
SQLAlchemy database models for the Student Result Management System.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Admin users who can log in and manage the system."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), default='Administrator')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    """A student record."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g. STU2026001
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(10))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    photo = db.Column(db.String(255), default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    marks = db.relationship('Marks', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'roll_number': self.roll_number,
            'department': self.department,
            'semester': self.semester,
            'section': self.section,
            'email': self.email,
            'phone': self.phone,
            'dob': self.dob,
            'gender': self.gender,
            'photo': self.photo,
        }


class Subject(db.Model):
    """A subject that can be assigned to a class/semester."""
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    max_marks = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    marks = db.relationship('Marks', backref='subject', lazy=True, cascade='all, delete-orphan')


class Marks(db.Model):
    """Marks obtained by a student in a subject across assessment types."""
    __tablename__ = 'marks'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)

    internal = db.Column(db.Float, default=0)     # out of 20
    mid_exam = db.Column(db.Float, default=0)      # out of 30
    final_exam = db.Column(db.Float, default=0)    # out of 50

    total = db.Column(db.Float, default=0)
    percentage = db.Column(db.Float, default=0)
    grade = db.Column(db.String(5))
    gpa = db.Column(db.Float, default=0)
    status = db.Column(db.String(10), default='Pass')  # Pass / Fail

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', name='uix_student_subject'),
    )

    GRADE_TABLE = [
        (90, 'O', 10.0),
        (80, 'A+', 9.0),
        (70, 'A', 8.0),
        (60, 'B+', 7.0),
        (50, 'B', 6.0),
        (40, 'C', 5.0),
        (0, 'F', 0.0),
    ]

    def compute(self):
        """Recompute total, percentage, grade, GPA and pass/fail status."""
        self.total = round((self.internal or 0) + (self.mid_exam or 0) + (self.final_exam or 0), 2)
        max_total = 100  # 20 + 30 + 50
        self.percentage = round((self.total / max_total) * 100, 2)

        for threshold, grade, gpa in self.GRADE_TABLE:
            if self.percentage >= threshold:
                self.grade = grade
                self.gpa = gpa
                break

        self.status = 'Fail' if self.percentage < 40 else 'Pass'


class Result(db.Model):
    """A per-semester aggregated result snapshot for a student (for ranking/report cards)."""
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    total_marks = db.Column(db.Float, default=0)
    total_max = db.Column(db.Float, default=0)
    percentage = db.Column(db.Float, default=0)
    gpa = db.Column(db.Float, default=0)
    overall_grade = db.Column(db.String(5))
    overall_status = db.Column(db.String(10), default='Pass')
    rank = db.Column(db.Integer)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref='results')
