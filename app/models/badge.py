from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime


class Badge(Document):
    meta = {
        "collection": "achievement_badge",
        "strict": False
    }

    name = StringField(required=True, unique=True)
    description = StringField(required=True)
    icon = StringField(default="🏅")
    condition_type = StringField(required=True)
    required_value = IntField(default=1)

    created_at = DateTimeField(default=datetime.utcnow)


class AchievementRecord(Document):
    meta = {
        "collection": "achievement_record",
        "indexes": [
            {
                "fields": ["user", "badge"],
                "unique": True
            }
        ],
        "strict": False
    }

    user = ReferenceField("User", required=True)
    badge = ReferenceField(Badge, required=True)
    unlocked_at = DateTimeField(default=datetime.utcnow)