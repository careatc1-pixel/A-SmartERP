@app.route('/hrm', methods=['GET', 'POST'])
@login_required
def hrm():
    if request.method == 'POST':
        last_s = Staff.query.order_by(Staff.id.desc()).first()
        emp_code = "AC101" if not last_s else f"AC{int(last_s.emp_code.replace('AC', '')) + 1}"
        new_staff = Staff(
            emp_code=emp_code, 
            name=request.form.get('name'), 
            designation=request.form.get('designation'),
            salary=float(request.form.get('salary')), 
            address=request.form.get('address')
        )
        db.session.add(new_staff); db.session.commit()
        return redirect(url_for('hrm'))
    
    all_s = Staff.query.all()
    today = datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    staff_list = []
    total_payroll = 0
    for s in all_s:
        # Live Salary Calculation
        p_count = Attendance.query.filter_by(staff_id=s.id, status='Present').count()
        h_count = Attendance.query.filter_by(staff_id=s.id, status='Half Day').count()
        payable_days = p_count + (h_count * 0.5)
        earned = round((s.salary / days_in_month) * payable_days, 2)
        total_payroll += earned
        staff_list.append({'info': s, 'earned': earned, 'days': payable_days})
        
    return render_template('hrm.html', staff_list=staff_list, total_payroll=total_payroll, name=current_user.username)