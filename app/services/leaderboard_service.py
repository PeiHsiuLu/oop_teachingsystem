from app.models.user import User


class LeaderboardService:
    def get_user_leaderboard(self, limit=10):
        collection = User._get_collection()

        users = list(collection.find())

        print("DEBUG raw user count:", len(users))

        ranking = []

        for user in users:
            username = user.get("username", "Unknown")
            role = user.get("role", "Unknown")
            xp = user.get("xp", 0) or 0
            level = user.get("level", 1) or 1
            credit_score = user.get("credit_score", 100) or 100

            print("DEBUG raw user:", username, role, xp, level, credit_score)

            ranking.append({
                "username": username,
                "role": role,
                "xp": xp,
                "level": level,
                "credit_score": credit_score
            })

        ranking.sort(key=lambda item: item["xp"], reverse=True)

        return ranking[:limit]