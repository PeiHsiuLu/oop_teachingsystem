from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.decorators import role_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    print(f"DEBUG: Current user is {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    # Because you are using the polymorphic '_cls' field in MongoEngine,
    # current_user.role will correctly return 'student' or 'admin'
    if current_user.role == 'student':
        return render_template('dashboard_student.html', user=current_user)
    elif current_user.role == 'admin':
        return render_template('dashboard_admin.html', user=current_user)
    
    return "Unknown Role", 403