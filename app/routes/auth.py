from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService() # Instantiate the service

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            auth_service.register(
                username=request.form['username'],
                email=request.form['email'],
                password=request.form['password'],
                role=request.form['role']
            )
            flash("Registration successful! Please log in.")
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e)) # Show "Username already taken" error
            
    return render_template('register.html')