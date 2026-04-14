from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import io
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Neon Connection
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_FORCE_ADMIN_2026'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

# ... Baki models wahi rahenge (Staff etc.) ...
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

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # --- FORCE ADMIN CREATION ---
    try:
        db.create_all()
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            new_admin = User(username='admin', password='password123')
            db.session.add(new_admin)
            db.session.commit()
            print("Admin created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")

    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('hrm'))
        else:
            return "Wrong Credentials. Try admin / password123"
    return render_template('login.html')

# ... Baki hrm aur logout routes wahi rahenge ...
@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        new_code = "AC101" if not last_s else f"AC{int(last_s.emp_code.replace('AC', '')) + 1}"
        new_staff = Staff(
            emp_code=new_code, name=request.form.get('name'),
            designation=request.form.get('designation'), salary=float(request.form.get('salary')),
            address=request.form.get('address'), aadhaar_no=request.form.get('aadhaar'),
            bank_acc=request.form.get('bank'), laptop_issued='laptop' in request.form,
            sim_issued='sim' in request.form, id_card_issued='id_card' in request.form
        )
        db.session.add(new_staff); db.session.commit()
        return redirect(url_for('hrm'))
    staff_list = Staff.query.all()
    return render_template('hrm.html', staff=staff_list, name=current_user.username)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))