import os, calendar, json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# NEON CONNECTION STRING (Aapka wala yahan)
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'A-SmartERP-Vikas-Secret'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- SQL MODELS ---
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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HRM ENGINE ---
@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        new_code = "AC101" if not last_s else f"AC{int(last_s.emp_code.replace('AC', '')) + 1}"
        
        new_s = Staff(emp_code=new_code, name=request.form.get('name'), 
                      designation=request.form.get('designation'), salary=float(request.form.get('salary')), 
                      address=request.form.get('address'))
        db.session.add(new_s); db.session.commit()
        return redirect(url_for('hrm'))
    
    all_staff = Staff.query.all()
    # Payroll logic
    today = datetime.now()
    days = calendar.monthrange(today.year, today.month)[1]
    
    staff_list = []
    for s in all_staff:
        presents = Attendance.query.filter_by(staff_id=s.id, status='Present').count()
        earned = round((s.salary / days) * presents, 2)
        staff_list.append({'info': s, 'earned': earned, 'days': presents})
        
    return render_template('hrm.html', staff_list=staff_list, name=current_user.username)

# --- QUICK ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u); return redirect(url_for('hrm'))
    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()
    app.run(debug=True)