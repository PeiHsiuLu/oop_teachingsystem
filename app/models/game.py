from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime


class Badge(Document):
    """
    Represents an achievement badge that students can earn.
    """
    badge_id = StringField(required=True, unique=True)
    name = StringField(required=True)
    description = StringField()
    criteria = StringField(required=True)
    icon_url = StringField()

    created_at = DateTimeField(default=datetime.utcnow)

    def is_earned(self, user_history):
        """
        Check whether the user meets the badge criteria.
        This can be expanded later based on XP, streak, completed tasks, etc.
        """
        return False

    def to_dict(self):
        return {
            "badge_id": self.badge_id,
            "name": self.name,
            "description": self.description,
            "criteria": self.criteria,
            "icon_url": self.icon_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class GameEvent(Document):
    """
    Records gamification events, such as earning XP or completing a task.
    """
    user = ReferenceField('User', required=True)
    event_type = StringField(required=True)  # e.g. vocabulary_review, dialogue_finished
    points = IntField(default=0)
    description = StringField()

    created_at = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "user_id": str(self.user.id) if self.user else None,
            "event_type": self.event_type,
            "points": self.points,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }