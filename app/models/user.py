from flask_login import UserMixin
from mongoengine import Document, StringField, IntField, ReferenceField, ListField,  BooleanField

class User(Document, UserMixin):
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    email = StringField(required=True)

    # Polymorphism configuration
    meta = {
        'allow_inheritance': True,
        'indexes': ['username']
    }

    def get_id(self):
        return str(self.id)
    
    @property
    def role(self):
        """Dynamically determine the user's role from the class name."""
        # The _cls field from MongoEngine holds the class name (e.g., 'User.Admin')
        return self._cls.split('.')[-1].lower()

class Admin(User):
    admin_level = IntField(default=1)
    # SRP: Admin uses CourseService

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

    def add_xp(self, amount):
        """
        Add XP to the student.
        """
        self.xp = getattr(self, "xp", 0) + amount
        self.save()