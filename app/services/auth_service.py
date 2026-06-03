from datetime import datetime

from flask_login import login_user, logout_user

from app import bcrypt
from app.repositories.user_repository import UserRepository
from app.models.user import Student, Admin


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, username, email, password, role="student"):
        """
        Register a new user as Student or Admin.
        """

        if self.user_repo.get_by_username(username):
            raise ValueError("Username already taken.")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        if role == "admin":
            new_user = Admin(
                username=username,
                email=email,
                password_hash=hashed_pw
            )
        else:
            new_user = Student(
                username=username,
                email=email,
                password_hash=hashed_pw
            )

        return self.user_repo.save(new_user)

    def login(self, username, password):
        """
        Login user.

        If login succeeds and the user is a Student:
        - Give +1 XP only once per day.
        - Multiple logins on the same day will not increase XP again.
        - Store reward status temporarily on the user object:
            user.daily_login_reward_added = True / False
        """

        user = self.user_repo.get_by_username(username)

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)

            if isinstance(user, Student):
                self._give_daily_login_reward(user)
            else:
                user.daily_login_reward_added = False

            return user

        return None

    def _give_daily_login_reward(self, user):
        """
        Give daily login reward.

        Rule:
        - Student can receive +1 XP once per day.
        - Multiple logins on the same day will not increase XP again.
        """

        now = datetime.now()
        today = now.date()

        last_reward_date = None

        if getattr(user, "last_login_reward_date", None):
            last_reward_date = user.last_login_reward_date.date()

        if last_reward_date == today:
            user.daily_login_reward_added = False
            return False

        user.add_xp(1)
        user.last_login_reward_date = now
        user.save()

        user.daily_login_reward_added = True

        try:
            from app.services.achievement_service import AchievementService

            achievement_service = AchievementService()
            achievement_service.check_level_badge(user)

        except Exception:
            pass

        return True

    def logout(self):
        """
        End the user session.
        """

        logout_user()
        return True

    def validate_role(self, user_id, required_role):
        """
        Check if a user has the required role to access a page.
        """

        user = self.user_repo.find_by_id(user_id)

        if not user:
            return False

        if required_role == "admin" and isinstance(user, Admin):
            return True

        if required_role == "student" and isinstance(user, Student):
            return True

        return False