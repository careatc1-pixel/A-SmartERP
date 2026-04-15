@app.route('/dashboard')
@login_required
def dashboard():
    # SaaS Logic: Yahan user ki specific info fetch ho rahi hai
    # Abhi ke liye hum admin data pass kar rahe hain, baad me ise dynamic karenge
    company_info = {
        "name": "Atharv Tech co.",
        "location": "New Delhi, India",
        "phone": "+91 93107 21874",
        "email": "care.atc1@gmail.com",
        "initial": "A"
    }
    
    invoices = Invoice.query.all()
    return render_template('dashboard.html', 
                           invoices=invoices, 
                           company=company_info, 
                           name=current_user.username)