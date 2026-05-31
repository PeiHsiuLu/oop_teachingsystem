import datetime
from mongoengine import Document, ReferenceField, IntField, StringField, DateTimeField, BooleanField

from app.models.user import Student
from app.models.word import Word


class VocabularyReviewLog(Document):
    user = ReferenceField(Student, required=True)
    word = ReferenceField(Word, required=True)

    quality = IntField(required=True)
    quality_label = StringField(required=True)

    is_successful = BooleanField(default=False)

    xp_gained = IntField(default=0)
    base_xp = IntField(default=0)
    bonus_xp = IntField(default=0)

    reviewed_at = DateTimeField(default=datetime.datetime.utcnow)
    next_review_at = DateTimeField()

    meta = {
        "collection": "vocabulary_review_logs",
        "ordering": ["-reviewed_at"]
    }