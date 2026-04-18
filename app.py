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
    SECRET_KEY='ATHARV_A_SUIT_SAAS_V1_MASTER' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- SAAS & SALES MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='Admin')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Isolation
    cust_code = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

class SaleInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Isolation
    inv_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    cancel_reason = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # SaaS Isolation
    so_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class DeliveryChallan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dc_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    vehicle_no = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class EWayBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ewb_no = db.Column(db.String(20), unique=True)
    inv_no = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentReceived(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    mode = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class CreditNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cn_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- SAAS CORE LOGIC ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/saas-init')
def init_saas():
    db.create_all()
    return "SaaS Tables Initialized!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form.get('password'))
        new_user = User(username=request.form.get('username'), password=hashed_pw, company_name=request.form.get('company'))
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

# --- MODULES WITH TENANT ISOLATION ---

@app.route('/dashboard')
@login_required
def dashboard():
    invoices = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.id.desc()).all()
    return render_template('dashboard.html', invoices=invoices, company=current_user.company_name, name=current_user.username)

@app.route('/sales/customers') 
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.name.asc()).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/approvals/orders')
@login_required
def approval_orders_page():
    data = SalesOrder.query.filter_by(user_id=current_user.id).order_by(SalesOrder.date.desc()).all()
    return render_template('approval_list.html', data=data, title="Sales Order Approval Queue", type='orders', name=current_user.username)

@app.route('/sales/delivery-challan')
@login_required
def delivery_challan():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('delivery_challan.html', customers=customers, name=current_user.username)

@app.route('/sales/eway-bills')
@login_required
def eway_bills():
    return render_template('eway_bills.html', name=current_user.username)

# --- VIEW & PRINT (SaaS Safe) ---

@app.route('/sales/view/<inv_no>')
@login_required
def view_invoice(inv_no):
    invoice = SaleInvoice.query.filter_by(inv_no=inv_no, user_id=current_user.id).first()
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', invoice=invoice, customers=customers, mode='print', name=current_user.username)

# --- API ENDPOINTS (SaaS Protected) ---

@app.route('/api/save-customer', methods=['POST'])
@login_required
def save_customer():
    data = request.json
    try:
        last_cust = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.id.desc()).first()
        next_id = (last_cust.id + 1) if last_cust else 1
        gen_code = f"ATC/CUST/{next_id:03d}"
        new_cust = Customer(user_id=current_user.id, cust_code=gen_code, name=data['name'], phone=data.get('phone'), gstin=data.get('gstin'), address=data.get('address'))
        db.session.add(new_cust)
        db.session.commit()
        return jsonify({"status": "success", "code": gen_code})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)