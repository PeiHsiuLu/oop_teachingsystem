from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.auth_service import AuthService
from flask_login import login_required

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
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), "error") # Show "Username already taken" error
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        success = auth_service.login(
            username=request.form['username'],
            password=request.form['password']
        )
        if success:
            flash('You were successfully logged in.', 'success')
            return redirect(url_for('main.index')) # Redirect to the new home page
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    auth_service.logout()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))