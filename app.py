from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import calendar, io, json, os

app = Flask(__name__)

# --- NEON SQL DATABASE CONFIG (Set with your URI) ---
NEON_DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Vercel/SQLAlchemy fix for postgres protocol
if NEON_DB_URL.startswith("postgres://"):
    NEON_DB_URL = NEON_DB_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = NEON_DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'A-SmartERP-Vikas-2026'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    address = db.Column(db.Text)
    # Relationship for cascade delete
    attendances = db.relationship('Attendance', backref='staff', cascade='all, delete-orphan')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.String(20))
    status = db.Column(db.String(20))
    punch_in = db.Column(db.String(20))
    punch_out = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/')
@login_required
def index(): 
    return redirect(url_for('hrm'))

@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        # AC101 Logic
        if not last_s:
            emp_code = "AC101"
        else:
            try:
                num = int(last_s.emp_code.replace("AC", ""))
                emp_code = f"AC{num + 1}"
            except:
                emp_code = f"AC{last_s.id + 101}"
        
        new_staff = Staff(
            emp_code=emp_code, 
            name=request.form.get('name'), 
            salary=float(request.form.get('salary')), 
            address=request.form.get('address')
        )
        db.session.add(new_staff)
        db.session.commit()
        return redirect(url_for('hrm'))
    
    all_s = Staff.query.all()
    days = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
    staff_list = []
    for s in all_s:
        p = Attendance.query.filter_by(staff_id=s.id, status='Present').count()
        earned = round((s.salary / days) * p, 2)
        staff_list.append({'info': s, 'earned': earned, 'days': p})
    
    return render_template('hrm.html', staff_list=staff_list, name=current_user.username)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Default Admin Creation
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()
    app.run(debug=True)