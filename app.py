from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import io
from datetime import datetime

app = Flask(__name__)

# Neon Connection Fix
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_INVOICE_PRO_2026'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(20), unique=True)
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Unpaid') # Unpaid, Paid
    date_created = db.Column(db.Date, default=datetime.utcnow().date())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    return redirect(url_for('login'))

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
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        last_inv = Invoice.query.order_by(Invoice.id.desc()).first()
        inv_no = "INV-101" if not last_inv else f"INV-{int(last_inv.invoice_no.split('-')[1]) + 1}"
        
        new_inv = Invoice(
            invoice_no=inv_no,
            client_name=request.form.get('client_name'),
            amount=float(request.form.get('amount')),
            status=request.form.get('status')
        )
        db.session.add(new_inv); db.session.commit()
        return redirect(url_for('dashboard'))
    
    invoices = Invoice.query.all()
    total_revenue = sum(inv.amount for inv in invoices if inv.status == 'Paid')
    return render_template('dashboard.html', invoices=invoices, total_revenue=total_revenue, name=current_user.username)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)