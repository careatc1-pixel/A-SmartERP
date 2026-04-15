from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from datetime import datetime
import pandas as pd
from io import BytesIO

# Vercel Production Variable
app = Flask(__name__)

# Neon Connection
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_ERP_V8_MASTER' # Key updated to trigger new table creation
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

# --- NEW MODELS ADDED (PURCHASE & INVENTORY LOG) ---

class PurchaseInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bill_no = db.Column(db.String(50), unique=True)
    vendor_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
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
    invoices = SaleInvoice.query.filter_by(user_id=current_user.id).order_by(SaleInvoice.id.desc()).all()
    return render_template('dashboard.html', invoices=invoices, company=company_info, name=current_user.username)

@app.route('/accounting')
@login_required
def accounting():
    user_sales = SaleInvoice.query.filter_by(user_id=current_user.id).all()
    total_val = sum(s.total_amount for s in user_sales)
    stats = { 
        "total_invoices": len(user_sales), 
        "pending_bills": 0, 
        "cash_flow": f"₹{total_val:,.2f}" 
    }
    return render_template('accounting.html', stats=stats, name=current_user.username)

@app.route('/sales/new')
@login_required
def new_sales():
    products = Product.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', products=products)

# --- SYNC ERROR FIX ROUTE ---
@app.route('/api/save-sale', methods=['POST'])
@login_required
def save_sale():
    data = request.json
    try:
        existing = SaleInvoice.query.filter_by(inv_no=data['inv_no']).first()
        final_inv_no = data['inv_no']
        if existing:
            final_inv_no = f"{data['inv_no']}-{datetime.now().strftime('%M%S')}"

        new_sale = SaleInvoice(
            user_id=current_user.id,
            inv_no=final_inv_no,
            client_name=data['client'],
            total_amount=float(data['total']),
            gst_amount=float(data['gst'])
        )
        db.session.add(new_sale)
        db.session.commit()
        return jsonify({"status": "success", "message": "Cloud Sync Complete"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

# --- NEW: MASTER EXPORT ROUTE (Sales, Purchase, Inventory) ---
@app.route('/export/<module>')
@login_required
def export_master(module):
    data_list = []
    filename = f"ATC_{module}_Report.xlsx"

    if module == 'sales':
        items = SaleInvoice.query.filter_by(user_id=current_user.id).all()
        data_list = [{
            "Date": i.date.strftime('%d-%m-%Y'),
            "Invoice No": i.inv_no,
            "Client": i.client_name,
            "GST Amount": i.gst_amount,
            "Total Amount": i.total_amount
        } for i in items]

    elif module == 'purchase':
        items = PurchaseInvoice.query.filter_by(user_id=current_user.id).all()
        data_list = [{
            "Date": i.date.strftime('%d-%m-%Y'),
            "Bill No": i.bill_no,
            "Vendor": i.vendor_name,
            "GST Amount": i.gst_amount,
            "Total Amount": i.total_amount
        } for i in items]

    elif module == 'inventory':
        items = Product.query.filter_by(user_id=current_user.id).all()
        data_list = [{
            "Item Name": i.name,
            "SKU": i.sku,
            "Current Stock": i.stock,
            "Unit Price": i.price,
            "Valuation": i.stock * i.price
        } for i in items]

    if not data_list:
        return "No data found to export", 404

    df = pd.DataFrame(data_list)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=module.capitalize())
    output.seek(0)
    
    return send_file(output, download_name=filename, as_attachment=True)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)