from app.repositories.base_repository import BaseRepository
from app.models.team import StudyGroup


class GroupRepository(BaseRepository):
    def __init__(self):
        super().__init__(StudyGroup)

    def get_group_by_member(self, user_id):
        return StudyGroup.objects(members=user_id).first()

    def get_leaderboard_data(self):
        return StudyGroup.objects.order_by("-created_at")

    def archive_group(self, group_id):
        group = self.find_by_id(group_id)
        if group:
            group.delete()
            return True
        return False