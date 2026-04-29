from mongoengine import Document, StringField, IntField, ReferenceField, ListField

class User(Document):
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    
    # Polymorphism configuration
    meta = {
        'allow_inheritance': True,
        'indexes': ['username']
    }

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
    
    # References are better than hard-coding IDs for flexible relationships
    # group = ReferenceField('StudyGroup') 

    def add_xp(self, amount):
        self.xp += amount
        self.save()

    def is_muted(self):
        return self.credit_score < 50