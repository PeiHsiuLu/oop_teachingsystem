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

    # Moderation / sanction notice
    # 管理員懲處通知
    sanction_notice = StringField(default="")
    sanction_type = StringField(default="")
    sanction_reason = StringField(default="")
    sanction_at = DateTimeField(default=None)
    sanction_seen = BooleanField(default=True)

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
        - credit_score <= 0 means the student is muted.

        判斷學生是否被禁言。
        目前規則：
        - credit_score <= 0 視為被禁言。
        """
        credit_score = getattr(self, "credit_score", 100)

        if credit_score is None:
            credit_score = 100

        return credit_score <= 0

    def can_send_message(self):
        """
        Return True if the student can send messages.
        """
        return not self.is_muted()

    def set_sanction_notice(self, sanction_type, notice, reason=""):
        """
        Save a sanction notice for the student.

        儲存管理員懲處通知。
        """
        from datetime import datetime

        self.sanction_type = sanction_type or ""
        self.sanction_notice = notice or ""
        self.sanction_reason = reason or ""
        self.sanction_at = datetime.utcnow()
        self.sanction_seen = False
        self.save()

    def clear_sanction_notice(self):
        """
        Mark sanction notice as seen.
        目前保留給之後加入「我知道了」按鈕使用。
        """
        self.sanction_seen = True
        self.save()