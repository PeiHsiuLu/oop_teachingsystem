from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services.auth_service import AuthService
from flask_login import login_required
from app.models.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService() # Instantiate the service

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            auth_service.register(
                username=form.username.data,
                email=form.email.data, # Access data from form object
                password=form.password.data,
                role=form.role.data
            )
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), "error") # Show "Username already taken" error
            
    return render_template('register.html',form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    print(f"DEBUG: Form validate_on_submit: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        user = auth_service.login(form.username.data, form.password.data)
        print(f"DEBUG: User object returned: {user}")
        
        if user:
            return redirect("/course/student/dashboard")
        else:
            flash('Invalid username or password.', 'error')
    else:
        print(f"DEBUG: Form errors: {form.errors}")
            
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    auth_service.logout()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))