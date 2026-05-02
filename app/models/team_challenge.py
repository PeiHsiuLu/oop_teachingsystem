from mongoengine import Document, StringField, IntField, DateTimeField, ReferenceField
from datetime import datetime
from app.models.team import StudyGroup


class TeamChallenge(Document):
    title = StringField(required=True)
    description = StringField()

    team = ReferenceField(StudyGroup, required=True)

    goal_type = StringField(default="xp")
    target_value = IntField(required=True)
    current_value = IntField(default=0)

    reward_xp = IntField(default=0)
    reward_credit = IntField(default=0)

    status = StringField(default="active")
    reward_claimed = StringField(default="no")

    deadline = DateTimeField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    completed_at = DateTimeField()

    def update_progress(self, value):
        if self.status == "completed":
            return

        self.current_value = value

        if self.current_value >= self.target_value:
            self.current_value = self.target_value
            self.status = "completed"
            self.completed_at = datetime.utcnow()

        self.save()

    def is_completed(self):
        return self.status == "completed"

    def progress_percent(self):
        if self.target_value == 0:
            return 0

        percent = int((self.current_value / self.target_value) * 100)
        return min(percent, 100)