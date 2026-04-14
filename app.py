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
    SECRET_KEY='ATHARV_TECH_2026_RESET'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- CLEAN MODELS ---
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

# --- AUTH ROUTES ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Auto-create tables and admin on first visit
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='password123'))
        db.session.commit()

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
        code = "ATC101" if not last else f"ATC{int(last.emp_code.replace('ATC', '')) + 1}"
        new_s = Staff(
            emp_code=code, name=request.form.get('name'), 
            designation=request.form.get('designation'), salary=float(request.form.get('salary')),
            laptop_issued='laptop' in request.form, id_card_issued='id_card' in request.form
        )
        db.session.add(new_s); db.session.commit()
        return redirect(url_for('hrm'))
    
    all_staff = Staff.query.all()
    # Payroll Placeholder for now
    staff_data = [{'info': s, 'earned': s.salary, 'payable': 30} for s in all_staff]
    
    return render_template('hrm.html', staff=staff_data, total_payroll=sum(s.salary for s in all_staff), name=current_user.username)

@app.route('/delete-staff/<int:id>')
@login_required
def delete_staff(id):
    s = Staff.query.get_or_404(id)
    db.session.delete(s); db.session.commit()
    return redirect(url_for('hrm'))