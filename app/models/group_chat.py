from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime

from app.models.team import StudyGroup
from app.models.user import User


class GroupChat(Document):
    group = ReferenceField(StudyGroup, required=True, unique=True)
    created_at = DateTimeField(default=datetime.utcnow)


class ChatMessage(Document):
    chat = ReferenceField(GroupChat, required=True)
    sender = ReferenceField(User, required=True)

    message_type = StringField(default="text")
    # text / voice

    content = StringField(required=True)
    # text message content
    # if voice message is added later, this can store audio file path or URL

    created_at = DateTimeField(default=datetime.utcnow)