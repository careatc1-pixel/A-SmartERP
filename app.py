# --- STAFF EDIT ROUTE ---
@app.route('/edit-staff/<int:id>', methods=['POST'])
@login_required
def edit_staff(id):
    s = Staff.query.get_or_404(id)
    s.name = request.form.get('name')
    s.salary = float(request.form.get('salary'))
    s.address = request.form.get('address')
    db.session.commit()
    return redirect(url_for('hrm'))

# --- STAFF DELETE ROUTE ---
@app.route('/delete-staff/<int:id>')
@login_required
def delete_staff(id):
    s = Staff.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for('hrm'))