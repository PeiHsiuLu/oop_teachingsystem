from datetime import datetime
from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField, BooleanField
class TeamChallenge(Document):
    group = ReferenceField("StudyGroup", required=True)
    created_by = ReferenceField("User", required=True)

    title = StringField(required=True)
    description = StringField()
    target_xp = IntField(required=True)
    current_xp = IntField(default=0)

    deadline = DateTimeField(required=True)
    is_completed = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)