from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, calendar
from datetime import datetime

app = Flask(__name__)

# Neon Connection Fix
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATC_FINAL_FORCE_2026'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- CLEAN & SOLID MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    salary = db.Column(db.Float, default=0.0)
    laptop_issued = db.Column(db.Boolean, default=False)
    id_card_issued = db.Column(db.Boolean, default=False)
    aadhaar = db.Column(db.String(20))
    bank_acc = db.Column(db.String(50))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date())
    status = db.Column(db.String(20)) # Full Day, Half Day, Short Leave

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    assigned_to = db.Column(db.Integer, db.ForeignKey('staff.id'))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MASTER ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('hrm'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last = Staff.query.order_by(Staff.id.desc()).first()
        code = "AC101" if not last else f"AC{int(last.emp_code.replace('AC', '')) + 1}"
        new_s = Staff(
            emp_code=code, name=request.form.get('name'), 
            designation=request.form.get('designation'), salary=float(request.form.get('salary')),
            aadhaar=request.form.get('aadhaar'), bank_acc=request.form.get('bank'),
            laptop_issued='laptop' in request.form, id_card_issued='id_card' in request.form
        )
        db.session.add(new_s); db.session.commit()
        return redirect(url_for('hrm'))
    
    # Safe data fetching with defaults
    staff_list = Staff.query.all()
    tasks_list = Task.query.all()
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    display_data = []
    total_payroll = 0.0
    for s in staff_list:
        full = Attendance.query.filter_by(staff_id=s.id, status='Full Day').count()
        half = Attendance.query.filter_by(staff_id=s.id, status='Half Day').count()
        payable = full + (half * 0.5)
        earned = round((s.salary / days_in_month) * payable, 2)
        total_payroll += earned
        display_data.append({'info': s, 'earned': earned, 'payable': payable})

    return render_template('hrm.html', staff=display_data, total_payroll=total_payroll, tasks=tasks_list, name=current_user.username)

if __name__ == '__main__':
    with app.app_context():
        # Dhyan dein: db.create_all() sirf naye tables banata hai, purane alter nahi karta.
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()
    app.run(debug=True)