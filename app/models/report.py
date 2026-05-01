from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime


class Report(Document):
    reporter = ReferenceField("User", required=True)
    target_user = ReferenceField("User")

    target_type = StringField(required=True)  # post, comment, user, team
    target_id = StringField(required=True)
    reason = StringField(required=True)
    status = StringField(default="pending")  # pending, resolved, archived
    created_at = DateTimeField(default=datetime.utcnow)

    def archive(self):
        self.status = "archived"
        self.save()

    def resolve(self):
        self.status = "resolved"
        self.save()