from app.repositories.base_repository import BaseRepository
from app.models.game import GameEvent
from app.models.badge import Badge

class BadgeRepository(BaseRepository):
    def __init__(self):
        super().__init__(Badge)

    def find_by_name(self, name):
        return Badge.objects(name=name).first()


class GameEventRepository(BaseRepository):
    def __init__(self):
        super().__init__(GameEvent)

    def find_by_user(self, user_id):
        return GameEvent.objects(user=user_id).order_by("-created_at")