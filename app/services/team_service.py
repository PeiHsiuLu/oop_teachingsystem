from app.models.team import StudyGroup
from datetime import datetime
from app.models.team_challenge import TeamChallenge

class TeamService:
    def create_group(self, name: str, description: str, user) -> StudyGroup:
        """UC7: Create a new Study Group."""
        # Check if name exists
        if StudyGroup.objects(name=name).first():
            raise ValueError("A team with this name already exists.")
            
        new_group = StudyGroup(name=name, description=description, leader=user)
        new_group.members.append(user) # Leader is automatically a member
        new_group.save()
        return new_group

    def join_group(self, group_id: str, user) -> bool:
        """UC7: Join an existing Study Group."""
        group = StudyGroup.objects(id=group_id).first()
        if not group:
            return False
            
        group.add_member(user)
        return True

    def get_all_groups(self):
        return StudyGroup.objects.all()
    def compute_leaderboard(self, group_id: str):
        group = StudyGroup.objects(id=group_id).first()
        
        if not group:
            raise ValueError("Group not found.")

        # 依照 XP 排序
        members = sorted(
            group.members,
            key=lambda user: getattr(user, "xp", 0),
            reverse=True
        )

        return [
            {
                "username": member.username,
                "xp": getattr(member, "xp", 0),
                "level": getattr(member, "level", 1)
            }
            for member in members
        ]



    def create_challenge(self, group_id, user, title, description, target_xp, deadline):
            group = StudyGroup.objects(id=group_id).first()

            if not group:
                raise ValueError("Group not found.")

            if user.role != "admin" and str(group.leader.id) != str(user.id):
                raise ValueError("You are not allowed to create a challenge.")

            challenge = TeamChallenge(
                group=group,
                created_by=user,
                title=title,
                description=description,
                target_xp=int(target_xp),
                deadline=datetime.strptime(deadline, "%Y-%m-%d")
            )

            challenge.save()
            return challenge
    def get_group_by_id(self, group_id):
        return StudyGroup.objects(id=group_id).first()
