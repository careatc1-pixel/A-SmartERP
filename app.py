from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os, calendar, io
from datetime import datetime
from reportlab.pdfgen import canvas # pip install reportlab

app = Flask(__name__)
DB_URL = "postgresql://neondb_owner:npg_h85KlFgYbsmE@ep-holy-breeze-amzy28jw-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SECRET_KEY'] = 'A-SmartERP-Pro-2026'

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# --- ROUTES & LOGIC ---

@app.route('/hrm')
@login_required
def hrm():
    # Calculation Logic: Attendance to Salary Slab
    all_s = Staff.query.all()
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    final_data = []
    for s in all_s:
        # Full = 1, Half = 0.5, Short = 0.75 (Custom Rules)
        full_days = Attendance.query.filter_by(staff_id=s.id, status='Full Day').count()
        half_days = Attendance.query.filter_by(staff_id=s.id, status='Half Day').count()
        
        payable_days = full_days + (half_days * 0.5)
        earned_salary = round((s.salary / days_in_month) * payable_days, 2)
        
        final_data.append({
            'info': s,
            'payable_days': payable_days,
            'earned': earned_salary
        })
    return render_template('hrm.html', staff=final_data, name=current_user.username)

# Offer Letter Generator (PDF)
@app.route('/generate-offer/<int:id>')
@login_required
def generate_offer(id):
    s = Staff.query.get(id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Atharv Tech Co. - Appointment Letter")
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Name: {s.name}")
    p.drawString(100, 730, f"Role: {s.designation}")
    p.drawString(100, 710, f"Salary: Rs. {s.salary} per month")
    p.drawString(100, 650, "Congratulations on joining the team!")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Offer_{s.name}.pdf")

# Task Assignment Route
@app.route('/assign-task', methods=['POST'])
@login_required
def assign_task():
    new_task = Task(
        task_title=request.form.get('title'),
        assigned_to=request.form.get('staff_id'),
        priority=request.form.get('priority')
    )
    db.session.add(new_task); db.session.commit()
    return redirect(url_for('tasks'))

if __name__ == '__main__':
    app.run(debug=True)