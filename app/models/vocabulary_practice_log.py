import datetime

from mongoengine import (
    Document,
    ReferenceField,
    StringField,
    BooleanField,
    DateTimeField
)

from app.models.user import Student
from app.models.word import Word


class VocabularyPracticeLog(Document):
    """
    Record each sentence practice attempt.

    This log records:
    - which student practiced
    - which word was practiced
    - what answer the student typed
    - what the correct answer was
    - whether the answer was correct
    - what CEFR level the student was at
    - when the practice happened
    """

    user = ReferenceField(Student, required=True)
    word = ReferenceField(Word, required=True)

    user_answer = StringField()
    correct_answer = StringField(required=True)

    is_correct = BooleanField(default=False)

    cefr_level_at_time = StringField(default="A1")

    practiced_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "vocabulary_practice_logs",
        "ordering": ["-practiced_at"]
    }