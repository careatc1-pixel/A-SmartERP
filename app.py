from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import io
from reportlab.pdfgen import canvas # PDF Library

app = Flask(__name__)

# Neon Connection
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_PHASE2_2026'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS (Phase 2: Full Onboarding) ---
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
    address = db.Column(db.Text)
    aadhaar_no = db.Column(db.String(20))
    bank_acc = db.Column(db.String(50))
    laptop_issued = db.Column(db.Boolean, default=False)
    sim_issued = db.Column(db.Boolean, default=False)
    id_card_issued = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
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

@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        # AUTO-INCREMENT EMP CODE (Starting AC101)
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        new_code = "AC101" if not last_s else f"AC{int(last_s.emp_code.replace('AC', '')) + 1}"
        
        new_staff = Staff(
            emp_code=new_code,
            name=request.form.get('name'),
            designation=request.form.get('designation'),
            salary=float(request.form.get('salary')),
            address=request.form.get('address'),
            aadhaar_no=request.form.get('aadhaar'),
            bank_acc=request.form.get('bank'),
            laptop_issued='laptop' in request.form,
            sim_issued='sim' in request.form,
            id_card_issued='id_card' in request.form
        )
        db.session.add(new_staff)
        db.session.commit()
        return redirect(url_for('hrm'))
    
    staff_list = Staff.query.all()
    return render_template('hrm.html', staff=staff_list, name=current_user.username)

# --- PDF OFFER LETTER GENERATOR ---
@app.route('/generate-offer/<int:id>')
@login_required
def generate_offer(id):
    s = Staff.query.get_or_404(id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(100, 800, "ATHARV TECH CO.")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 770, "Letter of Appointment")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Date: 15/04/2026")
    p.drawString(100, 700, f"Dear {s.name},")
    p.drawString(100, 680, f"We are pleased to appoint you as {s.designation} at our firm.")
    p.drawString(100, 660, f"Your Employee Code will be {s.emp_code} and your Monthly CTC")
    p.drawString(100, 640, f"will be Rs. {s.salary}/-.")
    p.drawString(100, 600, "Regards,")
    p.drawString(100, 580, "Management - Atharv Tech Co.")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Offer_{s.name}.pdf")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))