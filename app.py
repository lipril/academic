# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, Student, Result, Attendance, Assignment
from datetime import date
import os


# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure app settings
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')  # Vercel PostgreSQL or in-memory fallback
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Database setup and sample data seeding
with app.app_context():
    db.create_all()
    if os.environ.get('DATABASE_URL') and not Student.query.first():  # Seed only for persistent DB
        student = Student(student_id='CS001', name='John Doe')
        db.session.add(student)
        db.session.commit()
        result = Result(student_id=student.id, semester='Fall 2023', course='Data Structures', grade='A', credits=3, teacher='Dr. Smith')
        att = Attendance(student_id=student.id, date=date.today())
        assign = Assignment(student_id=student.id, course='Data Structures', title='Lab 1', due_date=date(2023, 12, 1), status='Completed')
        db.session.add_all([result, att, assign])
        db.session.commit()

# Route: Home/Login page
@app.route('/')
def login():
    return render_template('login.html')

# Route: API to get face encoding
@app.route('/get_face_encoding/<student_id>')
def get_face_encoding(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if student and student.face_encoding:
        return jsonify({'encoding': student.face_encoding.tolist()})
    return jsonify({'error': 'No encoding found'}), 404

# Route: Handle login
@app.route('/login', methods=['POST'])
def do_login():
    student_id = request.form['student_id']
    verification_token = request.form.get('verification_token')
    if verification_token == 'verified':
        session['student_id'] = student_id
        student = Student.query.filter_by(student_id=student_id).first()
        if student:
            today = date.today()
            if not Attendance.query.filter_by(student_id=student.id, date=today).first():
                new_att = Attendance(student_id=student.id, date=today)
                db.session.add(new_att)
                db.session.commit()
        return redirect(url_for('dashboard'))
    return "Verification failed."

# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))
    student = Student.query.filter_by(student_id=session['student_id']).first()
    results = Result.query.filter_by(student_id=student.id).all()
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    assignments = Assignment.query.filter_by(student_id=student.id).all()
    total_courses = len(results)
    completed = sum(1 for r in results if r.grade != 'F')
    due_assignments = [a for a in assignments if a.status == 'Due']
    return render_template('dashboard.html', student=student, results=results, attendance=attendance, assignments=assignments, total_courses=total_courses, completed=completed, due_assignments=due_assignments)

# Vercel handler
def handler(event, context):
    return app

if __name__ == '__main__':
    app.run(debug=True)


# In app.py, after db.init_app(app), add:
with app.app_context():
    try:
        db.create_all()
        print("Database connected successfully")
    except Exception as e:
        print(f"Database error: {e}")
