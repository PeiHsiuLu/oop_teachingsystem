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
            # 只有學生應該出現在學生排行榜。
            if not user_class.endswith("Student"):
                continue

            xp = user.get("xp", 0)
            level = user.get("level", 1)
            credit_score = user.get("credit_score", None)

            # Important:
            # Do NOT write: user.get("credit_score", 100) or 100
            # Because credit_score = 0 means muted, and 0 or 100 becomes 100.
            #
            # 重要：
            # 不可以寫成 user.get("credit_score", 100) or 100
            # 因為 credit_score = 0 代表被禁言，但 0 or 100 會變成 100。
            if xp is None:
                xp = 0

            if level is None:
                level = 1

            if credit_score is None:
                credit_score = 100

            ranking.append({
                "username": username,
                "role": "student",
                "xp": xp,
                "level": level,
                "credit_score": credit_score
            })

        ranking.sort(key=lambda item: item["xp"], reverse=True)

        return ranking[:limit]