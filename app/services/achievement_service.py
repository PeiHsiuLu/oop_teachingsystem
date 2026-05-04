from app.models.badge import Badge, AchievementRecord


class AchievementService:
    def seed_default_badges(self):
        default_badges = [
            {
                "name": "First Message",
                "description": "Send your first group chat message.",
                "icon": "💬",
                "condition_type": "first_message",
                "required_value": 1
            },
            {
                "name": "Team Challenger",
                "description": "Complete and claim a team challenge reward.",
                "icon": "🏆",
                "condition_type": "team_challenge_completed",
                "required_value": 1
            },
            {
                "name": "Level Up",
                "description": "Reach Level 2.",
                "icon": "⭐",
                "condition_type": "level_reached",
                "required_value": 2
            }
        ]

        for badge_data in default_badges:
            existing_badge = Badge.objects(name=badge_data["name"]).first()

            if not existing_badge:
                Badge(**badge_data).save()

    def unlock_badge(self, user, condition_type):
        badge = Badge.objects(condition_type=condition_type).first()

        if not badge:
            return None

        existing_record = AchievementRecord.objects(
            user=user,
            badge=badge
        ).first()

        if existing_record:
            return existing_record

        record = AchievementRecord(
            user=user,
            badge=badge
        )
        record.save()

        return record

    def check_level_badge(self, user):
        badge = Badge.objects(condition_type="level_reached").first()

        if not badge:
            return None

        if not hasattr(user, "level"):
            return None

        if user.level < badge.required_value:
            return None

        return self.unlock_badge(user, "level_reached")

    def get_user_achievements(self, user):
        return AchievementRecord.objects(user=user).order_by("-unlocked_at")