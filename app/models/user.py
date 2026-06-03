from flask_login import UserMixin
from mongoengine import Document, StringField, IntField, BooleanField


class User(Document, UserMixin):
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    email = StringField(required=True)

    # Polymorphism configuration
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
        - User.Admin -> admin
        - User.Student -> student
        """
        return self._cls.split(".")[-1].lower()


class Admin(User):
    admin_level = IntField(default=1)


class Student(User):
    xp = IntField(default=0)
    level = IntField(default=1)

    # Used by moderation system.
    # If credit_score <= 0, the student is treated as muted.
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

    def add_xp(self, amount):
        """
        Add XP to the student.
        """
        self.xp = getattr(self, "xp", 0) + amount
        self.save()

    def is_muted(self):
        """
        Return True if the student is muted.

        Current moderation rule:
        - credit_score <= 0 means the student is muted.
        """
        return getattr(self, "credit_score", 100) <= 0