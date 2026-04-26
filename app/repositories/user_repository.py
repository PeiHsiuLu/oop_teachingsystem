from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User) # Tell the base class to work with the User model

    def get_by_username(self, username):
        return User.objects(username=username).first()

    def update_credit_score(self, user_id, delta):
        user = self.find_by_id(user_id)
        if user:
            user.credit_score += delta
            user.save()

    def get_top_players(self, limit=10):
        # Sort by XP
        return User.objects.order_by('-xp')[:limit]