from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services.leaderboard_service import LeaderboardService
from app.models.course import LearningPath
from app.models.report import Report


dashboard_bp = Blueprint('dashboard', __name__)
leaderboard_service = LeaderboardService()


@dashboard_bp.route('/dashboard')
@login_required
def index():
    print(f"DEBUG: Current user is {current_user.username if current_user.is_authenticated else 'Anonymous'}")

    user_leaderboard = leaderboard_service.get_user_leaderboard(limit=10)

    if current_user.role == 'student':
        return render_template(
            'dashboard_student.html',
            user=current_user,
            user_leaderboard=user_leaderboard
        )

    elif current_user.role == 'admin':

        active_paths_count = LearningPath.objects.count()
        pending_reports_count = Report.objects(status="pending").count()

        return render_template(
            'dashboard_admin.html',
            user=current_user,
            user_leaderboard=user_leaderboard,
            active_paths=active_paths_count,
            pending_reports=pending_reports_count
        )

    return "Unknown Role", 403