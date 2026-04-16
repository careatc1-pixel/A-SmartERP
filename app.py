from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Neon Connection Setup
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_ERP_V17_CUSTOMER_MASTER' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
handler = app

# --- MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

# NAYA MODEL: CUSTOMER MASTER
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
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
        db.create_all() 
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    company_info = {"name": "Atharv Tech co.", "location": "New Delhi"}
    invoices = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.id.desc()).all()
    return render_template('dashboard.html', invoices=invoices, company=company_info, name=current_user.username)

@app.route('/accounting')
@login_required
def accounting():
    user_sales = SaleInvoice.query.filter_by(user_id=current_user.id).all()
    total_val = sum(s.total_amount for s in user_sales)
    stats = {"total_invoices": len(user_sales), "pending_bills": 0, "cash_flow": f"₹{total_val:,.2f}"}
    return render_template('accounting.html', stats=stats, name=current_user.username)

# --- SALES HUB & CUSTOMER MASTER ROUTES ---

@app.route('/sales/hub')
@login_required
def sales_hub():
    so_count = SalesOrder.query.filter_by(user_id=current_user.id, status='Pending').count()
    return render_template('sales_hub.html', so_count=so_count, name=current_user.username)

@app.route('/sales/customers') # CUSTOMER MASTER VIEW
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.name.asc()).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/new') # TAX INVOICE FORM (With Customer Dropdown)
@login_required
def new_sales():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

@app.route('/sales/order/new') # SALES ORDER FORM (With Customer Dropdown)
@login_required
def new_sales_order():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_order_form.html', customers=customers, name=current_user.username)

# --- APIs ---

@app.route('/api/save-customer', methods=['POST'])
@login_required
def save_customer():
    data = request.json
    try:
        new_cust = Customer(
            user_id=current_user.id,
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
            gst_amount=float(data['gst']),
            status='Pending'
        )
        db.session.add(new_sale)
        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/save-so', methods=['POST'])
@login_required
def save_so():
    data = request.json
    try:
        new_so = SalesOrder(
            user_id=current_user.id,
            so_no=data['so_no'],
            client_name=data['client'],
            total_amount=float(data['total']),
            status='Pending'
        )
        db.session.add(new_so)
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
            target = SalesOrder.query.filter_by(so_no=req['id']).first()
        else:
            target = SaleInvoice.query.filter_by(inv_no=req['id']).first()
        if target:
            target.status = req['status']
            if 'reason' in req: target.cancel_reason = req['reason']
            db.session.commit()
            return jsonify({"status": "success"})
        return jsonify({"status": "error"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/reports')
@login_required
def reports():
    sales = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.date.desc()).all()
    orders = SalesOrder.query.filter_by(user_id=current_user.id).order_by(SalesOrder.date.desc()).all()
    return render_template('reports.html', sales=sales, orders=orders, name=current_user.username)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)