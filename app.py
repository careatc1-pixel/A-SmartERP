from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, calendar
from datetime import datetime

# --- IMPORTANT: Vercel needs 'app' to be defined clearly ---
app = Flask(__name__)

# Neon Connection String
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'A-SmartERP-Pro-Key-2026'

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
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    salary = db.Column(db.Float)
    address = db.Column(db.Text)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date())
    status = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    # Direct check: login pe bhej raha hai ya nahi
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('hrm'))
    return render_template('login.html')

@app.route('/hrm')
@login_required
def hrm():
    all_s = Staff.query.all()
    # Basic logic for now to ensure page loads
    return render_template('hrm.html', staff_list=[], total_payroll=0, name=current_user.username)

# --- FOR VERCEL ---
# Don't use app.run() here for Vercel, it uses the 'app' object directly.