from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import pandas as pd
from io import BytesIO
from sqlalchemy import text

app = Flask(__name__)

# Neon Connection Setup
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_SAAS_ERP_V1_STABLE' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
handler = app

# --- SAAS MODELS (Integrated with Tenant Isolation) ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='Admin')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Key
    cust_code = db.Column(db.String(20))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Key
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)

class SaleInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Key
    inv_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancel_reason = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Key
    so_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancel_reason = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class DeliveryChallan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Key
    dc_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    vehicle_no = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- RECOVERY & INIT ROUTES ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/saas-init')
def saas_init():
    try:
        # Puraani crash tables uda kar SaaS ready tables banane ka force command
        db.session.execute(text("DROP TABLE IF EXISTS sale_invoice CASCADE;"))
        db.session.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE;"))
        db.session.commit()
        db.create_all()
        return "<h3>SaaS Environment Ready!</h3><a href='/register'>Register Company</a>"
    except Exception as e:
        return f"Error: {str(e)}"

# --- AUTH ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u: return "User already exists!"
        
        hashed_pw = generate_password_hash(request.form.get('password'))
        new_user = User(
            username=request.form.get('username'),
            password=hashed_pw,
            company_name=request.form.get('company')
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and check_password_hash(u.password, request.form.get('password')):
            login_user(u)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# --- CORE SAAS HUB ---

@app.route('/dashboard')
@login_required
def dashboard():
    # Show only current company's data
    invoices = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.id.desc()).all()
    return render_template('dashboard.html', invoices=invoices, company=current_user.company_name, name=current_user.username)

@app.route('/sales/hub')
@login_required
def sales_hub():
    so_count = SalesOrder.query.filter_by(user_id=current_user.id, status='Pending').count()
    return render_template('sales_hub.html', so_count=so_count, name=current_user.username)

@app.route('/sales/customers') 
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/new') 
@login_required
def new_sales():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

# --- API ENDPOINTS (SaaS Protected) ---

@app.route('/api/save-customer', methods=['POST'])
@login_required
def save_customer():
    data = request.json
    try:
        new_cust = Customer(
            user_id=current_user.id, # Multi-tenant lock
            name=data['name'], 
            email=data.get('email', ''), 
            phone=data.get('phone', ''), 
            gstin=data.get('gstin', ''), 
            address=data.get('address', '')
        )
        db.session.add(new_cust)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/update-status', methods=['POST'])
@login_required
def update_status():
    req = request.json
    try:
        if req['type'] == 'orders': 
            target = SalesOrder.query.filter_by(so_no=req['id'], user_id=current_user.id).first()
        else: 
            target = SaleInvoice.query.filter_by(inv_no=req['id'], user_id=current_user.id).first()
        
        if target:
            target.status = req['status']
            if 'reason' in req: target.cancel_reason = req['reason']
            db.session.commit()
            return jsonify({"status": "success"})
        return jsonify({"status": "error"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)