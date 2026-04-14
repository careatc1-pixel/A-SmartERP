# app.py ke routes wale section mein ye badlav karein

@app.route('/')
def index():
    # Agar user pehle se login hai toh HRM pe bhejo, nahi toh Login pe
    if current_user.is_authenticated:
        return redirect(url_for('hrm'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and u.password == request.form.get('password'):
            login_user(u)
            return redirect(url_for('hrm'))
        else:
            return "Invalid Credentials", 401
    return render_template('login.html')

# HRM route ke upar @login_required zaroor check karein
@app.route('/hrm')
@login_required
def hrm():
    # ... aapka purana hrm logic ...
    return render_template('hrm.html', staff_list=staff_list, name=current_user.username)