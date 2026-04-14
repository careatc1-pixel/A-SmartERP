from flask import Flask, render_template, redirect, url_for, request, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, calendar, io
from datetime import datetime
from reportlab.pdfgen import canvas # PDF Generation

app = Flask(__name__)

# Neon Connection
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATC_ULTRA_PRO_2026'
)

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
    aadhaar_no = db.Column(db.String(20))
    bank_acc = db.Column(db.String(50))
    laptop_issued = db.Column(db.Boolean, default=False)
    sim_issued = db.Column(db.Boolean, default=False)
    id_card_issued = db.Column(db.Boolean, default=False)

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

# --- ROUTES ---

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
    logout_user(); return redirect(url_for('login'))

@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last = Staff.query.order_by(Staff.id.desc()).first()
        code = "AC101" if not last else f"AC{int(last.emp_code.replace('AC', '')) + 1}"
        new_s = Staff(
            emp_code=code, name=request.form.get('name'), 
            designation=request.form.get('designation'), salary=float(request.form.get('salary')),
            aadhaar_no=request.form.get('aadhaar'), bank_acc=request.form.get('bank'),
            laptop_issued='laptop' in request.form, id_card_issued='id_card' in request.form
        )
        db.session.add(new_s); db.session.commit()
        return redirect(url_for('hrm'))
    
    all_staff = Staff.query.all()
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    staff_data = []
    total_payroll = 0
    for s in all_staff:
        # Attendance logic for earned salary
        full = Attendance.query.filter_by(staff_id=s.id, status='Full Day').count()
        half = Attendance.query.filter_by(staff_id=s.id, status='Half Day').count()
        short = Attendance.query.filter_by(staff_id=s.id, status='Short Leave').count()
        
        payable = full + (half * 0.5) + (short * 0.75)
        earned = round((s.salary / days_in_month) * payable, 2)
        total_payroll += earned
        staff_data.append({'info': s, 'earned': earned, 'payable': payable})

    tasks = Task.query.all()
    return render_template('hrm.html', staff=staff_data, total_payroll=total_payroll, tasks=tasks, name=current_user.username)

# Offer Letter Logic
@app.route('/offer-letter/<int:id>')
@login_required
def offer_letter(id):
    s = Staff.query.get(id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "OFFER LETTER - Atharv Tech Co.")
    p.drawString(100, 700, f"Name: {s.name}")
    p.drawString(100, 680, f"Role: {s.designation}")
    p.drawString(100, 660, f"Monthly Salary: {s.salary}")
    p.showPage(); p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Offer_{s.name}.pdf")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)