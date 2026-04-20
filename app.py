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
    SECRET_KEY='ATHARV_SAAS_FINAL_STABLE' 
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(100))
    subscribed_modules = db.Column(db.String(255), default='sales') 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- DATABASE AUTO-REPAIR FUNCTION ---
def repair_database():
    try:
        with app.app_context():
            # Zabardasti missing columns add karna
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS company_name VARCHAR(100)'))
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS subscribed_modules VARCHAR(255) DEFAULT \'sales\''))
            db.session.commit()
    except Exception as e:
        print(f"DB Repair Skip: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    repair_database() # Pehle DB theek karega phir register
    if request.method == 'POST':
        try:
            hashed_pw = generate_password_hash(request.form.get('password'))
            modules = ",".join(request.form.getlist('modules')) or 'sales'
            
            new_user = User(
                username=request.form.get('username'),
                password=hashed_pw,
                company_name=request.form.get('company'),
                subscribed_modules=modules
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
        # Dono check: Plain Text (purana) aur Hashed (naya)
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
        # Crash-proof module handling
        modules = current_user.subscribed_modules.split(',') if current_user.subscribed_modules else ['sales']
        return render_template('dashboard.html', 
                               user_modules=modules, 
                               company=current_user.company_name or "ATC Workspace", 
                               username=current_user.username)
    except Exception as e:
        return f"Dashboard Error: {str(e)}"

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)