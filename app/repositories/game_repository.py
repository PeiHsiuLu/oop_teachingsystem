from app.repositories.base_repository import BaseRepository
from app.models.game import Badge, GameEvent


class BadgeRepository(BaseRepository):
    def __init__(self):
        super().__init__(Badge)

    def find_by_badge_id(self, badge_id):
        return Badge.objects(badge_id=badge_id).first()


class GameEventRepository(BaseRepository):
    def __init__(self):
        super().__init__(GameEvent)

    def find_by_user(self, user_id):
        return GameEvent.objects(user=user_id).order_by("-created_at")