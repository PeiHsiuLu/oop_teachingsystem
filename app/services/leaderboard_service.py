from app.models.user import User


class LeaderboardService:
    def get_user_leaderboard(self, limit=50):
        collection = User._get_collection()

        users = list(collection.find())

        ranking = []

        for user in users:
            username = user.get("username", "Unknown")

            # MongoEngine inheritance stores role information in _cls.
            # Example:
            # - User.Student
            # - User.Admin
            user_class = user.get("_cls", "")

            # Only students should appear on the account leaderboard.
            if not user_class.endswith("Student"):
                continue

            xp = user.get("xp", 0) or 0
            level = user.get("level", 1) or 1
            credit_score = user.get("credit_score", 100) or 100

            ranking.append({
                "username": username,
                "role": "student",
                "xp": xp,
                "level": level,
                "credit_score": credit_score
            })

        ranking.sort(key=lambda item: item["xp"], reverse=True)

        return ranking[:limit]