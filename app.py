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

# --- MODELS (SaaS Ready with Full Profiles) ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False) 
    company_name = db.Column(db.String(100))
    # Profile Fields
    contact_no = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    subscribed_modules = db.Column(db.String(255), default='sales') 

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

# --- DATABASE AUTO-REPAIR FUNCTION ---
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
            return True
    except Exception as e:
        db.session.rollback()
        return False

# --- ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/force-sync-db')
def force_sync():
    if repair_database():
        return "<h3>Database Sync Successful!</h3><a href='/register'>Go to Register</a>"
    return "<h3>Database Sync Failed!</h3>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    repair_database() 
    if request.method == 'POST':
        try:
            hashed_pw = generate_password_hash(request.form.get('password'))
            modules_list = request.form.getlist('modules')
            modules_str = ",".join(modules_list) if modules_list else 'sales'
            
            new_user = User(
                username=request.form.get('username'),
                password=hashed_pw,
                company_name=request.form.get('company'),
                contact_no=request.form.get('contact'),
                email=request.form.get('email'),
                address=request.form.get('address'),
                subscribed_modules=modules_str
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return f"Registration Error: {str(e)}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        pass_input = request.form.get('password')
        if u:
            if u.password == pass_input or check_password_hash(u.password, pass_input):
                login_user(u)
                return redirect(url_for('dashboard'))
        return "Invalid Login! Please check credentials."
    return render_template('login_form.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user_modules = current_user.subscribed_modules.split(',') if current_user.subscribed_modules else ['sales']
        comp_name = current_user.company_name if current_user.company_name else "ATC Workspace"
        return render_template('dashboard.html', 
                               user_modules=user_modules, 
                               company=comp_name, 
                               username=current_user.username)
    except Exception as e:
        return f"Dashboard Access Error: {str(e)}"

# --- MAIN SALES HUB ROUTE ---

@app.route('/sales/hub')
@login_required
def sales_hub():
    if 'sales' not in current_user.subscribed_modules:
        return "<h3>Access Denied: Module not in your plan.</h3><a href='/dashboard'>Back</a>"
    so_count = SalesOrder.query.filter_by(user_id=current_user.id, status='Pending').count()
    return render_template('sales_hub.html', so_count=so_count, name=current_user.username)

# --- SALES HUB SUB-MODULE ROUTES (RESTORED) ---

@app.route('/sales/customers') 
@login_required
def customer_master():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('customer_master.html', customers=customers, name=current_user.username)

@app.route('/sales/invoice/new')
@login_required
def new_invoice():
    # Tax Invoice logic
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('sales_form.html', customers=customers, name=current_user.username)

@app.route('/sales/order/new')
@login_required
def new_sales_order():
    # Sales Order / Quotation logic
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

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)