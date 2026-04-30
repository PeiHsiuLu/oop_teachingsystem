from mongoengine import Document, ReferenceField, DateTimeField, IntField, ListField, StringField
from datetime import datetime

class InteractionLog(Document):
    """
    Records the interaction behavior of a student (Use Case 4_2).
    """
    user_id = ReferenceField('Student', required=True)
    unit_id = ReferenceField('Unit', required=False) # Optional for global practice
    timestamp = DateTimeField(default=datetime.utcnow)
    correctness_score = IntField(default=0)
    time_spent = IntField(default=0) # Recorded in seconds
    clicked_options = ListField(StringField())

    def to_dict(self):
        return {
            "user_id": str(self.user_id.id),
            "unit_id": str(self.unit_id.id) if self.unit_id else None,
            "timestamp": self.timestamp.isoformat(),
            "correctness_score": self.correctness_score,
            "time_spent": self.time_spent,
            "clicked_options": self.clicked_options
        }