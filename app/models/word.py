from mongoengine import Document, StringField, ListField, IntField, ReferenceField, DateTimeField, CASCADE, FloatField
import datetime

class Word(Document):
    """Represents a single word in the vocabulary database."""
    word_text = StringField(required=True, unique=True)
    definition = StringField(required=True)
    part_of_speech = StringField() # e.g., 'noun', 'verb', 'adjective'
    example_sentences = ListField(StringField()) # Example sentences for the word
    difficulty_level = IntField(default=1, min_value=1, max_value=5) # 1: easy, 5: hard

    meta = {
        'collection': 'words',
        'indexes': [
            'word_text',
            'difficulty_level'
        ]
    }

class SentenceGeneratingRule(Document):
    """Defines rules for automatically generating sentences."""
    rule_name = StringField(required=True, unique=True)
    pattern = StringField(required=True) # A string representing a rule pattern (e.g., "Subject Verb Object")
    keywords = ListField(StringField()) # Keywords associated with this rule to trigger its use
    difficulty_level = IntField(default=1, min_value=1, max_value=5)

    meta = {
        'collection': 'sentence_generating_rules',
        'indexes': [
            'rule_name',
            'difficulty_level'
        ]
    }

class ReviewItem(Document):
    """Tracks a student's review progress for a specific word."""
    # Reference to the User model (assuming 'User' is defined in app.models.user)
    user = ReferenceField('User', required=True, reverse_delete_rule=CASCADE)
    # Reference to the Word model
    word = ReferenceField('Word', required=True, reverse_delete_rule=CASCADE)
    
    # SRS Fields
    due_date = DateTimeField(default=datetime.datetime.utcnow) # When the item is next due for review
    interval = IntField(default=0) # The gap in days until the next review
    ease_factor = FloatField(default=2.5) # A multiplier that affects the interval
    
    # General tracking fields
    last_reviewed = DateTimeField(default=datetime.datetime.utcnow)
    review_count = IntField(default=0)

    meta = {
        'collection': 'review_items',
        'indexes': [
            {'fields': ('user', 'word'), 'unique': True}, # A user can only have one review item per word
            'user',
            'due_date' # Crucial for efficiently finding words to review
        ]
    }