from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.badge import Badge, AchievementRecord


achievement_bp = Blueprint(
    "achievement",
    __name__,
    url_prefix="/achievements"
)


@achievement_bp.route("/")
@login_required
def my_achievements():
    records = AchievementRecord.objects(
        user=current_user._get_current_object()
    ).order_by("-unlocked_at")

    unlocked_badge_ids = [record.badge.id for record in records]

    all_badges = Badge.objects()

    return render_template(
        "achievements.html",
        records=records,
        all_badges=all_badges,
        unlocked_badge_ids=unlocked_badge_ids
    )