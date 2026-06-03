from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.services.achievement_service import AchievementService


achievement_bp = Blueprint(
    "achievement",
    __name__,
    url_prefix="/achievements"
)

achievement_service = AchievementService()


@achievement_bp.route("/")
@login_required
def my_achievements():
    user = current_user._get_current_object()

    achievement_data = achievement_service.get_achievement_page_data(user)

    return render_template(
        "achievements.html",
        achievements=achievement_data["achievements"],
        unlocked_count=achievement_data["unlocked_count"],
        total_count=achievement_data["total_count"],
        completion_rate=achievement_data["completion_rate"],
        stats=achievement_data["stats"]
    )