from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from mongoengine import Document, EmbeddedDocument, StringField, FloatField, IntField, DateTimeField, EmbeddedDocumentListField, ReferenceField

class Word(EmbeddedDocument):
    """
    Represents a single vocabulary word in a student's VocabularyBank.

    This class holds the word itself, its definition, and spaced repetition
    metadata like ease_factor and the next_review_date.
    """
    word = StringField(required=True)
    definition = StringField(required=True)
    category = StringField()
    ease_factor = FloatField(default=2.5)
    interval = IntField(default=0)
    next_review_date = DateTimeField(default=datetime.utcnow)
    last_reviewed = DateTimeField()

    def calculate_next_interval(self, performance_rating: int):
        """
        Updates the word's review interval based on student performance.

        This is a simplified implementation of the SM-2 spaced repetition algorithm.
        In a full implementation, this logic would be handled by the
        `srs_strategy.py` service to adhere to the Strategy Pattern.

        Args:
            performance_rating (int): A student's self-assessed rating of recall (e.g., 0-5).
        """
        if performance_rating < 3:
            # Failed recall, reset interval
            self.interval = 1
        else:
            # Successful recall
            if self.interval == 0:
                self.interval = 1
            elif self.interval == 1:
                self.interval = 6
            else:
                self.interval = round(self.interval * self.ease_factor)

            # Adjust ease factor
            self.ease_factor += (0.1 - (5 - performance_rating) * (0.08 + (5 - performance_rating) * 0.02))
            if self.ease_factor < 1.3:
                self.ease_factor = 1.3

        self.next_review_date = datetime.utcnow() + timedelta(days=self.interval)
        self.last_reviewed = datetime.utcnow()

class VocabularyBank(Document):
    """
    Represents a student's entire collection of vocabulary words.

    This class acts as a container for Word objects and is designed to be
    embedded within or linked from a Student document in MongoDB.
    """
    user_id = ReferenceField('Student', required=True, unique=True)
    list_of_words = EmbeddedDocumentListField(Word)

    def add_word(self, word_item: Word):
        """Adds a new word to the bank if it doesn't already exist."""
        if not any(w.word == word_item.word for w in self.list_of_words):
            self.list_of_words.append(word_item)
            self.save()

    def get_words_due_for_review(self) -> List[Word]:
        """Returns a list of words that are due for review."""
        now = datetime.utcnow()
        return [word for word in self.list_of_words if word.next_review_date <= now]