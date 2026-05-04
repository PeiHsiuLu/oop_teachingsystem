class LevelSystem:
    XP_PER_LEVEL = 100

    def calculate_level(self, xp):
        if xp is None:
            xp = 0

        if xp < 0:
            xp = 0

        return (xp // self.XP_PER_LEVEL) + 1

    def update_user_level(self, user):
        if not hasattr(user, "xp"):
            return user

        new_level = self.calculate_level(user.xp)

        if hasattr(user, "level"):
            user.level = new_level
            user.save()

        return user