from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.badge import Badge, AchievementRecord
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

    # Make sure default badges exist.
    achievement_service.seed_default_badges()

    # Retroactive check:
    # If the user is already Level 2 or above,
    # unlock the Level Up achievement when they visit this page.
    achievement_service.check_level_badge(user)

    records = AchievementRecord.objects(
        user=user
    ).order_by("-unlocked_at")

    unlocked_badge_ids = [record.badge.id for record in records]

    all_badges = Badge.objects()

    return render_template(
        "achievements.html",
        records=records,
        all_badges=all_badges,
        unlocked_badge_ids=unlocked_badge_ids
    )