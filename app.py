"""
Student Result Management System
---------------------------------
A Flask + SQLAlchemy + SQLite web app for managing students, subjects,
marks and results, with report card generation and basic analytics.

Run with:
    pip install -r requirements.txt
    python app.py
"""
import os
import io
import csv
import shutil
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, jsonify, send_file, abort
)
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_

from config import Config
from models import db, User, Student, Subject, Marks, Result

# --------------------------------------------------------------------------
# App / extension setup
# --------------------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# --------------------------------------------------------------------------
# Auth helpers
# --------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {
        'college_name': app.config['COLLEGE_NAME'],
        'current_year': datetime.utcnow().year,
        'logged_in_user': session.get('username'),
    }


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter(
            or_(User.username == username, User.email == username)
        ).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    total_students = Student.query.count()
    total_subjects = Subject.query.count()
    total_results = Marks.query.count()

    all_marks = Marks.query.all()
    if all_marks:
        passed = [m for m in all_marks if m.status == 'Pass']
        failed = [m for m in all_marks if m.status == 'Fail']
        pass_percentage = round(len(passed) / len(all_marks) * 100, 1)
        average_marks = round(sum(m.percentage for m in all_marks) / len(all_marks), 1)
    else:
        pass_percentage = 0
        average_marks = 0
        failed = []

    top_result = Result.query.order_by(Result.percentage.desc()).first()

    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    recent_marks = Marks.query.order_by(Marks.created_at.desc()).limit(5).all()

    grade_counts = {}
    for m in all_marks:
        grade_counts[m.grade] = grade_counts.get(m.grade, 0) + 1

    return render_template(
        'dashboard.html',
        total_students=total_students,
        total_subjects=total_subjects,
        total_results=total_results,
        pass_percentage=pass_percentage,
        failed_students=len(set(m.student_id for m in failed)),
        average_marks=average_marks,
        top_result=top_result,
        recent_students=recent_students,
        recent_marks=recent_marks,
        grade_counts=grade_counts,
    )


# --------------------------------------------------------------------------
# Student management
# --------------------------------------------------------------------------
def generate_student_id():
    year = datetime.utcnow().year
    count = Student.query.count() + 1
    candidate = f"STU{year}{count:04d}"
    while Student.query.filter_by(student_id=candidate).first():
        count += 1
        candidate = f"STU{year}{count:04d}"
    return candidate


@app.route('/students')
@login_required
def students():
    q = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Student.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Student.name.ilike(like),
            Student.roll_number.ilike(like),
            Student.student_id.ilike(like),
        ))
    if department:
        query = query.filter(Student.department == department)

    pagination = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    departments = [d[0] for d in db.session.query(Student.department).distinct()]

    return render_template(
        'students.html',
        students=pagination.items,
        pagination=pagination,
        departments=departments,
        q=q,
        selected_department=department,
    )


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()

        if not name or not roll_number or not department or not semester:
            flash('Name, roll number, department and semester are required.', 'error')
            return redirect(url_for('add_student'))

        if Student.query.filter_by(roll_number=roll_number).first():
            flash('A student with this roll number already exists.', 'error')
            return redirect(url_for('add_student'))

        photo_filename = 'default.png'
        photo = request.files.get('photo')
        if photo and photo.filename and allowed_file(photo.filename):
            photo_filename = secure_filename(f"{roll_number}_{photo.filename}")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        student = Student(
            student_id=generate_student_id(),
            name=name,
            roll_number=roll_number,
            department=department,
            semester=semester,
            section=request.form.get('section', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            dob=request.form.get('dob', '').strip(),
            gender=request.form.get('gender', '').strip(),
            photo=photo_filename,
        )
        db.session.add(student)
        db.session.commit()
        flash(f'Student "{student.name}" added with ID {student.student_id}.', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html')


@app.route('/students/<int:sid>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(sid):
    student = Student.query.get_or_404(sid)

    if request.method == 'POST':
        student.name = request.form.get('name', '').strip()
        student.department = request.form.get('department', '').strip()
        student.semester = request.form.get('semester', '').strip()
        student.section = request.form.get('section', '').strip()
        student.email = request.form.get('email', '').strip()
        student.phone = request.form.get('phone', '').strip()
        student.dob = request.form.get('dob', '').strip()
        student.gender = request.form.get('gender', '').strip()

        photo = request.files.get('photo')
        if photo and photo.filename and allowed_file(photo.filename):
            photo_filename = secure_filename(f"{student.roll_number}_{photo.filename}")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            student.photo = photo_filename

        db.session.commit()
        flash('Student details updated.', 'success')
        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)


@app.route('/students/<int:sid>/delete', methods=['POST'])
@login_required
def delete_student(sid):
    student = Student.query.get_or_404(sid)
    db.session.delete(student)
    db.session.commit()
    flash(f'Student "{student.name}" deleted.', 'success')
    return redirect(url_for('students'))


@app.route('/api/students/search')
@login_required
def api_students_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    results = Student.query.filter(or_(
        Student.name.ilike(like),
        Student.roll_number.ilike(like),
        Student.student_id.ilike(like),
    )).limit(10).all()
    return jsonify([s.to_dict() for s in results])


# --------------------------------------------------------------------------
# Subject management
# --------------------------------------------------------------------------
@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        name = request.form.get('name', '').strip()
        department = request.form.get('department', '').strip()
        semester = request.form.get('semester', '').strip()
        max_marks = request.form.get('max_marks', 100, type=int)

        if not code or not name or not department or not semester:
            flash('All subject fields are required.', 'error')
            return redirect(url_for('subjects'))

        if Subject.query.filter_by(code=code).first():
            flash('A subject with this code already exists.', 'error')
            return redirect(url_for('subjects'))

        subject = Subject(code=code, name=name, department=department,
                           semester=semester, max_marks=max_marks)
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{name}" added.', 'success')
        return redirect(url_for('subjects'))

    all_subjects = Subject.query.order_by(Subject.department, Subject.semester).all()
    return render_template('subjects.html', subjects=all_subjects)


@app.route('/subjects/<int:sub_id>/edit', methods=['POST'])
@login_required
def edit_subject(sub_id):
    subject = Subject.query.get_or_404(sub_id)
    subject.name = request.form.get('name', subject.name).strip()
    subject.department = request.form.get('department', subject.department).strip()
    subject.semester = request.form.get('semester', subject.semester).strip()
    subject.max_marks = request.form.get('max_marks', subject.max_marks, type=int)
    db.session.commit()
    flash('Subject updated.', 'success')
    return redirect(url_for('subjects'))


@app.route('/subjects/<int:sub_id>/delete', methods=['POST'])
@login_required
def delete_subject(sub_id):
    subject = Subject.query.get_or_404(sub_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted.', 'success')
    return redirect(url_for('subjects'))


# --------------------------------------------------------------------------
# Marks management
# --------------------------------------------------------------------------
@app.route('/marks')
@login_required
def marks():
    all_marks = Marks.query.order_by(Marks.updated_at.desc()).all()
    return render_template('marks.html', marks_list=all_marks)


@app.route('/marks/add', methods=['GET', 'POST'])
@login_required
def add_marks():
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        internal = request.form.get('internal', 0, type=float)
        mid_exam = request.form.get('mid_exam', 0, type=float)
        final_exam = request.form.get('final_exam', 0, type=float)

        if not student_id or not subject_id:
            flash('Please select a student and a subject.', 'error')
            return redirect(url_for('add_marks'))

        existing = Marks.query.filter_by(student_id=student_id, subject_id=subject_id).first()
        record = existing or Marks(student_id=student_id, subject_id=subject_id)
        record.internal = internal
        record.mid_exam = mid_exam
        record.final_exam = final_exam
        record.compute()

        if not existing:
            db.session.add(record)
        db.session.commit()
        recalculate_result(student_id)

        flash('Marks saved and grade calculated.', 'success')
        return redirect(url_for('marks'))

    all_students = Student.query.order_by(Student.name).all()
    all_subjects = Subject.query.order_by(Subject.name).all()
    return render_template('add_marks.html', students=all_students, subjects=all_subjects)


@app.route('/marks/<int:mark_id>/delete', methods=['POST'])
@login_required
def delete_marks(mark_id):
    record = Marks.query.get_or_404(mark_id)
    student_id = record.student_id
    db.session.delete(record)
    db.session.commit()
    recalculate_result(student_id)
    flash('Marks record deleted.', 'success')
    return redirect(url_for('marks'))


@app.route('/api/marks/calculate', methods=['POST'])
@login_required
def api_calculate_marks():
    """Live-calculate total/percentage/grade/GPA for the add-marks form."""
    data = request.get_json(force=True) or {}
    temp = Marks(
        internal=float(data.get('internal') or 0),
        mid_exam=float(data.get('mid_exam') or 0),
        final_exam=float(data.get('final_exam') or 0),
    )
    temp.compute()
    return jsonify({
        'total': temp.total,
        'percentage': temp.percentage,
        'grade': temp.grade,
        'gpa': temp.gpa,
        'status': temp.status,
    })


# --------------------------------------------------------------------------
# Results & ranking
# --------------------------------------------------------------------------
def recalculate_result(student_id):
    """Recompute the aggregated Result row for a student and refresh ranks."""
    student = Student.query.get(student_id)
    if not student:
        return

    student_marks = Marks.query.filter_by(student_id=student_id).all()
    if not student_marks:
        Result.query.filter_by(student_id=student_id).delete()
        db.session.commit()
        return

    total_marks = sum(m.total for m in student_marks)
    total_max = len(student_marks) * 100
    percentage = round(total_marks / total_max * 100, 2) if total_max else 0
    gpa = round(sum(m.gpa for m in student_marks) / len(student_marks), 2)
    overall_status = 'Fail' if any(m.status == 'Fail' for m in student_marks) else 'Pass'

    for threshold, grade, _ in Marks.GRADE_TABLE:
        if percentage >= threshold:
            overall_grade = grade
            break

    result = Result.query.filter_by(student_id=student_id, semester=student.semester).first()
    if not result:
        result = Result(student_id=student_id, semester=student.semester)
        db.session.add(result)

    result.total_marks = total_marks
    result.total_max = total_max
    result.percentage = percentage
    result.gpa = gpa
    result.overall_grade = overall_grade
    result.overall_status = overall_status
    result.generated_at = datetime.utcnow()
    db.session.commit()

    recompute_ranks(student.semester)


def recompute_ranks(semester):
    results = Result.query.filter_by(semester=semester).order_by(Result.percentage.desc()).all()
    for idx, r in enumerate(results, start=1):
        r.rank = idx
    db.session.commit()


@app.route('/results')
@login_required
def results():
    all_results = Result.query.order_by(Result.percentage.desc()).all()
    return render_template('results.html', results=all_results)


@app.route('/results/<int:student_id>/report-card')
@login_required
def report_card(student_id):
    student = Student.query.get_or_404(student_id)
    student_marks = Marks.query.filter_by(student_id=student_id).all()
    result = Result.query.filter_by(student_id=student_id, semester=student.semester).first()
    subject_map = {s.id: s for s in Subject.query.all()}

    return render_template(
        'report_card.html',
        student=student,
        marks_list=student_marks,
        result=result,
        subject_map=subject_map,
        today=datetime.utcnow().strftime('%d %B %Y'),
    )


# --------------------------------------------------------------------------
# Analytics (used by dashboard/results charts via Chart.js on the frontend)
# --------------------------------------------------------------------------
@app.route('/api/analytics/subject-averages')
@login_required
def api_subject_averages():
    rows = db.session.query(
        Subject.name, func.avg(Marks.percentage)
    ).join(Marks, Marks.subject_id == Subject.id).group_by(Subject.name).all()
    return jsonify({'labels': [r[0] for r in rows], 'data': [round(r[1], 1) for r in rows]})


@app.route('/api/analytics/grade-distribution')
@login_required
def api_grade_distribution():
    rows = db.session.query(Marks.grade, func.count(Marks.id)).group_by(Marks.grade).all()
    return jsonify({'labels': [r[0] for r in rows], 'data': [r[1] for r in rows]})


@app.route('/api/analytics/top-students')
@login_required
def api_top_students():
    top = Result.query.order_by(Result.percentage.desc()).limit(10).all()
    return jsonify({
        'labels': [r.student.name for r in top],
        'data': [r.percentage for r in top],
    })


# --------------------------------------------------------------------------
# Profile & settings
# --------------------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', user.full_name).strip()
        user.email = request.form.get('email', user.email).strip()
        db.session.commit()
        session['full_name'] = user.full_name
        flash('Profile updated.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_password':
            current = request.form.get('current_password', '')
            new = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            if not user.check_password(current):
                flash('Current password is incorrect.', 'error')
            elif new != confirm:
                flash('New passwords do not match.', 'error')
            elif len(new) < 6:
                flash('New password must be at least 6 characters.', 'error')
            else:
                user.set_password(new)
                db.session.commit()
                flash('Password changed successfully.', 'success')
        return redirect(url_for('settings'))
    return render_template('settings.html', user=user)


@app.route('/settings/backup')
@login_required
def backup_database():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = os.path.join(os.path.dirname(__file__), backup_name)
    shutil.copy(db_path, backup_path)
    return send_file(backup_path, as_attachment=True, download_name=backup_name)


@app.route('/settings/restore', methods=['POST'])
@login_required
def restore_database():
    file = request.files.get('backup_file')
    if not file or not file.filename.endswith('.db'):
        flash('Please upload a valid .db backup file.', 'error')
        return redirect(url_for('settings'))

    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    db.session.remove()
    db.engine.dispose()
    file.save(db_path)
    flash('Database restored. Please log in again.', 'success')
    session.clear()
    return redirect(url_for('login'))


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
@app.route('/export/students/csv')
@login_required
def export_students_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Name', 'Roll Number', 'Department', 'Semester', 'Section', 'Email', 'Phone'])
    for s in Student.query.all():
        writer.writerow([s.student_id, s.name, s.roll_number, s.department, s.semester, s.section, s.email, s.phone])

    mem = io.BytesIO(output.getvalue().encode('utf-8'))
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='students.csv')


@app.route('/export/results/csv')
@login_required
def export_results_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Rank', 'Student', 'Roll Number', 'Semester', 'Percentage', 'GPA', 'Grade', 'Status'])
    for r in Result.query.order_by(Result.percentage.desc()).all():
        writer.writerow([r.rank, r.student.name, r.student.roll_number, r.semester,
                          r.percentage, r.gpa, r.overall_grade, r.overall_status])

    mem = io.BytesIO(output.getvalue().encode('utf-8'))
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='results.csv')


# --------------------------------------------------------------------------
# Error handlers
# --------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def too_large(e):
    flash('Uploaded file is too large (max 5 MB).', 'error')
    return redirect(request.referrer or url_for('dashboard'))


# --------------------------------------------------------------------------
# CLI: initialize database with a default admin account
# --------------------------------------------------------------------------
@app.cli.command('init-db')
def init_db_command():
    """Create tables and a default admin user (flask init-db)."""
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@srms.local', full_name='System Admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Default admin created -> username: admin | password: admin123')
    else:
        print('Database already initialized.')


def ensure_bootstrap():
    """Auto-create tables + default admin on first run (so `python app.py` just works)."""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@srms.local', full_name='System Admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()


if __name__ == '__main__':
    ensure_bootstrap()
    app.run(debug=True)
