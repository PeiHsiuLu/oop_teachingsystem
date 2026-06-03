from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    ReferenceField
)


class Report(Document):
    meta = {
        "strict": False,
        "indexes": [
            "status",
            "target_type",
            "target_id",
            "created_at"
        ]
    }

    reporter = ReferenceField("User", required=True)
    target_user = ReferenceField("User")

    target_type = StringField(required=True)  # user, chat_message, team, post, comment
    target_id = StringField(required=True)
    reason = StringField(required=True)

    status = StringField(default="pending")  # pending, resolved, archived
    created_at = DateTimeField(default=datetime.utcnow)

    handled_by = ReferenceField("User")
    handled_at = DateTimeField()
    action_taken = StringField(default="")  # resolved, archived, warning, mute

    def resolve(self, handled_by=None, action_taken="resolved"):
        self.status = "resolved"
        self.handled_by = handled_by
        self.handled_at = datetime.utcnow()
        self.action_taken = action_taken
        self.save()

    def archive(self, handled_by=None):
        self.status = "archived"
        self.handled_by = handled_by
        self.handled_at = datetime.utcnow()
        self.action_taken = "archived"
        self.save()

    def apply_action(self, handled_by=None, action_taken="resolved"):
        self.status = "resolved"
        self.handled_by = handled_by
        self.handled_at = datetime.utcnow()
        self.action_taken = action_taken
        self.save()