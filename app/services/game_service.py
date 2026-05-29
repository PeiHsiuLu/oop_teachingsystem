from app.models.user import User
from app.models.game import GameEvent
from app.models.badge import Badge
from app.services.achievement_service import AchievementService


class GameManager:
    def __init__(self):
        self.achievement_service = AchievementService()

    def process_event(self, event_type, user_id, data=None):
        user = User.objects(id=user_id).first()
        if not user:
            return None

        points = self.calculate_points(event_type, data)

        if hasattr(user, "add_xp"):
            user.add_xp(points)
        else:
            user.xp = getattr(user, "xp", 0) + points
            user.save()

        event = GameEvent(
            user=user,
            event_type=event_type,
            points=points
        )
        event.save()

        self.achievement_service.unlock_badge(user, event_type)

        return event

    def calculate_points(self, event_type, data=None):
        points_map = {
            "vocabulary_review": 10,
            "dialogue_finished": 20,
            "join_team": 5,
            "create_team": 10
        }
        return points_map.get(event_type, 1)

    def check_and_award_badge(self, user):
        badges = Badge.objects.all()
        earned = []

        for badge in badges:
            if badge.is_earned(user):
                earned.append(badge)

        return earned