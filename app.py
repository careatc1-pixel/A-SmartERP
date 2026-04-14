from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, calendar
from datetime import datetime

app = Flask(__name__)

# --- NEON SQL DATABASE CONFIG ---
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'A-SmartERP-Pro-2026-Vikas'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    salary = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(20))
    status = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTH ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('hrm'))
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
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- HRM ROUTES ---

@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        emp_code = "AC101" if not last_s else f"AC{int(last_s.emp_code.replace('AC', '')) + 1}"
        new_staff = Staff(
            emp_code=emp_code, 
            name=request.form.get('name'), 
            designation=request.form.get('designation'),
            salary=float(request.form.get('salary')), 
            address=request.form.get('address')
        )
        db.session.add(new_staff)
        db.session.commit()
        return redirect(url_for('hrm'))
    
    all_s = Staff.query.all()
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    staff_list = []
    total_payroll = 0
    for s in all_s:
        p_count = Attendance.query.filter_by(staff_id=s.id, status='Present').count()
        earned = round((s.salary / days_in_month) * p_count, 2)
        total_payroll += earned
        staff_list.append({'info': s, 'earned': earned, 'days': p_count})
        
    return render_template('hrm.html', staff_list=staff_list, total_payroll=total_payroll, name=current_user.username)

@app.route('/delete-staff/<int:id>')
@login_required
def delete_staff(id):
    s = Staff.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('hrm'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()
    app.run(debug=True)