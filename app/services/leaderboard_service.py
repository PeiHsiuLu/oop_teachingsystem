from app.models.user import User


class LeaderboardService:
    def get_user_leaderboard(self, limit=10):
        users = User.objects()

        ranking = []

        for user in users:
            ranking.append({
                "username": getattr(user, "username", "Unknown"),
                "role": getattr(user, "role", "Unknown"),
                "xp": getattr(user, "xp", 0),
                "level": getattr(user, "level", 1),
                "credit_score": getattr(user, "credit_score", 100)
            })

        ranking.sort(key=lambda item: item["xp"], reverse=True)

        return ranking[:limit]