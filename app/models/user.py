from flask_login import UserMixin
from mongoengine import (
    Document,
    StringField,
    IntField,
    DateTimeField,
    BooleanField
)


class User(Document, UserMixin):
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    email = StringField(required=True)

    meta = {
        "allow_inheritance": True,
        "indexes": ["username"]
    }

    def get_id(self):
        return str(self.id)

    @property
    def role(self):
        """
        Dynamically determine the user's role from the class name.

        Example:
        User.Admin -> admin
        User.Student -> student
        """
        return self._cls.split(".")[-1].lower()


class Admin(User):
    admin_level = IntField(default=1)


class Student(User):
    xp = IntField(default=0)
    level = IntField(default=1)
    credit_score = IntField(default=100)

    cefr_level = StringField(
        choices=["A1", "A2", "B1", "B2", "C1", "C2"],
        default="A1"
    )

    cefr_total_answered = IntField(default=0)
    cefr_correct_answered = IntField(default=0)
    cefr_correct_streak = IntField(default=0)

    has_seen_vocabulary_practice_guide = BooleanField(default=False)

    vocabulary_review_count = IntField(default=0)

    # Daily login reward record
    # 每日登入獎勵紀錄：用來避免同一天重複領取 XP
    last_login_reward_date = DateTimeField(default=None)

    def add_xp(self, amount):
        """
        Add XP to the student.
        """
        if amount is None:
            amount = 0

        current_xp = getattr(self, "xp", 0) or 0
        self.xp = current_xp + int(amount)
        self.save()

    def is_muted(self):
        """
        Check whether the student is muted.

        Current project rule:
        - When an admin applies the "mute" sanction, report_service.py sets credit_score to 0.
        - Therefore, credit_score <= 0 means the student is muted.

        判斷學生是否被禁言。

        目前專案規則：
        - 管理員在檢舉處理中套用 mute 時，report_service.py 會把 credit_score 設為 0。
        - 因此 credit_score <= 0 就視為被禁言。
        """
        credit_score = getattr(self, "credit_score", 100)

        if credit_score is None:
            credit_score = 100

        return credit_score <= 0

    def can_send_message(self):
        """
        Return True if the student can send chat/dialogue messages.
        """
        return not self.is_muted()