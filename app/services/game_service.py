from app.models.user import User
from app.models.game import GameEvent, Badge


class GameManager:
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

        self.check_and_award_badge(user)

        return event

    def calculate_points(self, event_type, data=None):
        if event_type == "vocabulary_review":
            return 10
        if event_type == "dialogue_finished":
            return 20
        if event_type == "join_team":
            return 5
        if event_type == "create_team":
            return 10
        return 1

    def check_and_award_badge(self, user):
        badges = Badge.objects.all()
        earned = []

        for badge in badges:
            if badge.is_earned(user):
                earned.append(badge)

        return earned