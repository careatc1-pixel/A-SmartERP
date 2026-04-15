from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime

# Vercel needs this "app" variable to be clearly defined
app = Flask(__name__)

# Neon Connection
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_FORCE_V5'
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Vercel handler
handler = app

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
    status = db.Column(db.String(20), default='Unpaid')
    date_created = db.Column(db.Date, default=datetime.utcnow().date())

# --- NAYE MODELS (SALES & INVENTORY) ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)

class SaleInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    inv_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Paid')
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    with app.app_context():
        db.create_all() # Saare naye tables yahan ban jayenge
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='password123'))
            db.session.commit()

    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    company_info = {
        "name": "Atharv Tech co.",
        "location": "New Delhi, India",
        "phone": "+91 93107 21874",
        "email": "care.atc1@gmail.com",
        "initial": "A"
    }
    invoices = Invoice.query.all()
    return render_template('dashboard.html', invoices=invoices, company=company_info, name=current_user.username)

@app.route('/accounting')
@login_required
def accounting():
    stats = { "total_invoices": 124, "pending_bills": 12, "cash_flow": "₹4,50,000" }
    return render_template('accounting.html', stats=stats, name=current_user.username)

# --- NAYE ROUTES (SALES FUNCTIONALITY) ---
@app.route('/sales/new')
@login_required
def new_sales():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', products=products)

@app.route('/api/save-sale', methods=['POST'])
@login_required
def save_sale():
    data = request.json
    try:
        new_sale = SaleInvoice(
            user_id=current_user.id,
            inv_no=data['inv_no'],
            client_name=data['client'],
            total_amount=float(data['total']),
            gst_amount=float(data['gst'])
        )
        db.session.add(new_sale)
        db.session.commit()
        return jsonify({"status": "success", "message": "Sale Recorded"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)