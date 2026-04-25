from mongoengine import Document, StringField, IntField, ReferenceField, ListField

class User(Document):
    username = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    
    # Polymorphism configuration
    meta = {'allow_inheritance': True}

class Admin(User):
    admin_level = IntField(default=1)

    def create_learning_path(self, name):
        # Logic to set up new LearningPaths
        pass

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