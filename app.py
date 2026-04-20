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
    SECRET_KEY='ATHARV_SAAS_V5_STRICT_SESSION_RESET' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
handler = app

# --- MODELS (Tenant Isolated & SaaS Ready) ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    company_name = db.Column(db.String(100))
    subscribed_modules = db.Column(db.String(255), default='sales') 
    role = db.Column(db.String(20), default='Admin')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cust_code = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

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
    status = db.Column(db.String(20), default='Pending')
    cancel_reason = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    so_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancel_reason = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- RECOVERY & INIT ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/force-init-saas')
def init_saas():
    try:
        db.create_all()
        return "SaaS Tables Initialized!"
    except Exception as e:
        return f"Init Error: {str(e)}"

# --- CORE SAAS ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html') 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'))
        selected_modules = ",".join(request.form.getlist('modules')) or 'sales'
        
        new_user = User(
            username=request.form.get('username'),
            password=hashed_pw,
            company_name=request.form.get('company'),
            subscribed_modules=selected_modules
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
        return "Invalid Username or Password!"
    return render_template('login_form.html')

# --- CRASH-PROOF DASHBOARD ---

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Check subscribed modules with fallback
        if hasattr(current_user, 'subscribed_modules') and current_user.subscribed_modules:
            user_modules = current_user.subscribed_modules.split(',')
        else:
            user_modules = ['sales'] 
        
        # Safe fetch company name
        comp_name = getattr(current_user, 'company_name', 'My Workspace')
        
        return render_template('dashboard.html', 
                               user_modules=user_modules, 
                               company=comp_name, 
                               username=current_user.username)
    except Exception as e:
        db.session.rollback()
        return f"Dashboard Error: {str(e)}. Please run /force-init-saas"

# --- PROTECTED ERP MODULES ---

@app.route('/sales/hub')
@login_required
def sales_hub():
    if 'sales' not in current_user.subscribed_modules:
        return "<h3>Access Denied: Sales Module not purchased.</h3><a href='/dashboard'>Back</a>"
    so_count = SalesOrder.query.filter_by(user_id=current_user.id, status='Pending').count()
    return render_template('sales_hub.html', so_count=so_count, name=current_user.username)

@app.route('/sales/customers') 
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.name.asc()).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/new') 
@login_required
def new_sales():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

# --- API ENDPOINTS ---

@app.route('/api/save-customer', methods=['POST'])
@login_required
def save_customer():
    data = request.json
    try:
        new_cust = Customer(user_id=current_user.id, name=data['name'], email=data.get('email', ''), phone=data.get('phone', ''), gstin=data.get('gstin', ''), address=data.get('address', ''))
        db.session.add(new_cust)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)