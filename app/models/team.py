from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField
from datetime import datetime

class StudyGroup(Document):
    """
    Represents a team or study group (Use Case 7: Team Up).
    Students can create, join, and manage these groups.
    """
    name = StringField(required=True, unique=True, max_length=100)
    description = StringField(max_length=500)
    leader = ReferenceField('User', required=True) # The student who created the team
    members = ListField(ReferenceField('User'))
    created_at = DateTimeField(default=datetime.utcnow)

    def add_member(self, user):
        if user not in self.members:
            self.members.append(user)
            self.save()
    def remove_member(self, user):
        if user in self.members:
            self.members.remove(user)
            self.save()