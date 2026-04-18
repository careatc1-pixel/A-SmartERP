from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
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
    SECRET_KEY='ATHARV_ERP_V32_FULL_RESTORE' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
handler = app

# --- MODELS START ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cust_code = db.Column(db.String(50), nullable=True) 
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

class DeliveryChallan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dc_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    vehicle_no = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentReceived(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    mode = db.Column(db.String(50))
    ref_no = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class CreditNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cn_no = db.Column(db.String(50), unique=True)
    inv_ref = db.Column(db.String(50)) 
    client_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    reason = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class EWayBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ewb_no = db.Column(db.String(20), unique=True)
    inv_no = db.Column(db.String(50))
    transporter = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    gstin = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    po_no = db.Column(db.String(50), unique=True)
    vendor_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseBill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bill_no = db.Column(db.String(50), unique=True)
    vendor_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class DebitNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dn_no = db.Column(db.String(50), unique=True)
    vendor_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    reason = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- MODELS END ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- SPECIAL RE-SYNC ROUTE ---
@app.route('/force-sync-db')
def force_sync():
    try:
        db.session.execute(text("DROP TABLE IF EXISTS customer CASCADE;"))
        db.session.commit()
        db.create_all()
        return "<h3>Success!</h3><p>Database Matched. Customer Master Active.</p><a href='/sales/customers'>Open Master</a>"
    except Exception as e:
        return f"SQL Error: {str(e)}"

# --- CORE ROUTES ---

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

@app.route('/sales/hub')
@login_required
def sales_hub():
    so_count = SalesOrder.query.filter_by(user_id=current_user.id, status='Pending').count()
    return render_template('sales_hub.html', so_count=so_count, name=current_user.username)

# --- SALES MANAGEMENT ROUTES ---

@app.route('/sales/approvals/orders')
@login_required
def approval_orders_page():
    data = SalesOrder.query.filter_by(user_id=current_user.id).order_by(SalesOrder.date.desc()).all()
    return render_template('approval_list.html', data=data, title="Sales Order Approval Queue", type='orders', name=current_user.username)

@app.route('/sales/approvals/invoices')
@login_required
def approval_invoices_page():
    data = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.date.desc()).all()
    return render_template('approval_list.html', data=data, title="Tax Invoice Approval Queue", type='invoices', name=current_user.username)

@app.route('/sales/customers') 
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).order_by(Customer.id.desc()).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/new') 
@login_required
def new_sales():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

@app.route('/sales/order/new') 
@login_required
def new_sales_order():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_order_form.html', customers=customers, name=current_user.username)

# --- SALES EXTRA MODULES ROUTES ---

@app.route('/sales/delivery-challan')
@login_required
def delivery_challan():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('delivery_challan.html', customers=customers, name=current_user.username)

@app.route('/sales/payments')
@login_required
def payments_received():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('payments_received.html', customers=customers, name=current_user.username)

@app.route('/sales/credit-notes')
@login_required
def credit_notes():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('credit_notes.html', customers=customers, name=current_user.username)

@app.route('/sales/eway-bills')
@login_required
def eway_bills():
    return render_template('eway_bills.html', name=current_user.username)

# --- PURCHASE HUB ROUTES ---

@app.route('/purchase/hub')
@login_required
def purchase_hub():
    return render_template('purchase_hub.html', name=current_user.username)

@app.route('/purchase/vendors')
@login_required
def vendor_master():
    vendors = Vendor.query.filter_by(user_id=current_user.id).all()
    return render_template('vendor_master.html', vendors=vendors, name=current_user.username)

# --- VIEW & PRINT ROUTES ---

@app.route('/sales/view/<inv_no>')
@login_required
def view_invoice(inv_no):
    invoice = SaleInvoice.query.filter_by(inv_no=inv_no, user_id=current_user.id).first()
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', invoice=invoice, customers=customers, mode='print', name=current_user.username)

@app.route('/sales/order/view/<so_no>')
@login_required
def view_sales_order(so_no):
    order = SalesOrder.query.filter_by(so_no=so_no, user_id=current_user.id).first()
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_order_form.html', order=order, customers=customers, mode='print', name=current_user.username)

# --- API ENDPOINTS ---

@app.route('/api/save-customer', methods=['POST'])
@login_required
def save_customer():
    data = request.json
    try:
        last_cust = Customer.query.order_by(Customer.id.desc()).first()
        next_id = (last_cust.id + 1) if last_cust else 1
        generated_code = f"ATC/CUST/{next_id:03d}"
        new_cust = Customer(user_id=current_user.id, cust_code=generated_code, name=data['name'], email=data.get('email', ''), phone=data.get('phone', ''), gstin=data.get('gstin', ''), address=data.get('address', ''))
        db.session.add(new_cust)
        db.session.commit()
        return jsonify({"status": "success", "code": generated_code})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "SQL Error: Run /force-sync-db"}), 400

@app.route('/api/save-sale', methods=['POST'])
@login_required
def save_sale():
    data = request.json
    try:
        new_sale = SaleInvoice(user_id=current_user.id, inv_no=data['inv_no'], client_name=data['client'], total_amount=float(data['total']), gst_amount=float(data['gst']), status='Pending')
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
        new_so = SalesOrder(user_id=current_user.id, so_no=data['so_no'], client_name=data['client'], total_amount=float(data['total']), status='Pending')
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
        if req['type'] == 'orders': target = SalesOrder.query.filter_by(so_no=req['id']).first()
        else: target = SaleInvoice.query.filter_by(inv_no=req['id']).first()
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