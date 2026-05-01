from mongoengine import Document, StringField, DateTimeField
from datetime import datetime
class Report(Document):
    report_id = StringField(required=True, unique=True)
    reporter_id = StringField(required=True)
    target_user_id = StringField(required=True)
    target_type = StringField(required=True)  # post, comment, user
    target_id = StringField(required=True)
    reason = StringField(required=True)
    status = StringField(default="pending")  # pending, resolved, archived
    created_at = DateTimeField(default=datetime.now)

    def archive(self):
        self.status = "archived"
        self.save()

    def resolve(self):
        self.status = "resolved"
        self.save()