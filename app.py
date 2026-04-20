from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import text

app = Flask(__name__)

# Neon Connection Setup
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='ATHARV_SAAS_V5_STABLE_FINAL' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False) 
    company_name = db.Column(db.String(100))
    contact_no = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    subscribed_modules = db.Column(db.String(255), default='sales') 

class SaleInvoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    inv_no = db.Column(db.String(50), unique=True)
    client_name = db.Column(db.String(100))
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class SalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    so_no = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE AUTO-REPAIR ---
def repair_database():
    try:
        with app.app_context():
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(500)'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS company_name VARCHAR(100)'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS contact_no VARCHAR(20)'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email VARCHAR(100)'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS address TEXT'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS subscribed_modules VARCHAR(255) DEFAULT \'sales\''))
            db.session.commit()
    except Exception as e:
        db.session.rollback()

# --- CORE ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    repair_database() 
    if request.method == 'POST':
        try:
            hashed_pw = generate_password_hash(request.form.get('password'))
            modules_list = request.form.getlist('modules')
            modules_str = ",".join(modules_list) if modules_list else 'sales'
            new_user = User(username=request.form.get('username'), password=hashed_pw, company_name=request.form.get('company'), contact_no=request.form.get('contact'), email=request.form.get('email'), address=request.form.get('address'), subscribed_modules=modules_str)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return f"Error: {str(e)}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        pass_input = request.form.get('password')
        if u and (u.password == pass_input or check_password_hash(u.password, pass_input)):
            login_user(u)
            return redirect(url_for('dashboard'))
    return render_template('login_form.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_modules = current_user.subscribed_modules.split(',') if current_user.subscribed_modules else ['sales']
    return render_template('dashboard.html', user_modules=user_modules, company=current_user.company_name, username=current_user.username)

# --- SALES HUB & SUB-MODULES (RESTORED) ---

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

@app.route('/sales/invoice/new') # TAX INVOICE FIX
@login_required
def new_invoice():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

@app.route('/sales/eway-bills') # E-WAY BILL FIX
@login_required
def eway_bills():
    return render_template('eway_bills.html', name=current_user.username)

@app.route('/sales/order/new')
@login_required
def new_sales_order():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_order_form.html', customers=customers, name=current_user.username)

@app.route('/sales/delivery-challan')
@login_required
def delivery_challan_page():
    return render_template('delivery_challan.html', name=current_user.username)

@app.route('/sales/payments')
@login_required
def payments_page():
    return render_template('payments.html', name=current_user.username)

@app.route('/sales/credit-notes')
@login_required
def credit_notes_page():
    return render_template('credit_notes.html', name=current_user.username)

# --- VIEW & PRINT ROUTES ---
@app.route('/sales/view/<inv_no>')
@login_required
def view_invoice(inv_no):
    invoice = SaleInvoice.query.filter_by(inv_no=inv_no, user_id=current_user.id).first()
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', invoice=invoice, customers=customers, mode='print', name=current_user.username)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)