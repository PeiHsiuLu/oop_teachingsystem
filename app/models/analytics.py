from mongoengine import Document, ReferenceField, DateTimeField, StringField, DynamicField, CASCADE
import datetime

class InteractionLog(Document):
    """
    Logs a specific user interaction for later analysis.
    This collection can grow very large, so indexing is critical.
    """
    user = ReferenceField('User', required=True, reverse_delete_rule=CASCADE)
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    
    # Type of event, e.g., 'WORD_REVIEW', 'DIALOGUE_CHOICE', 'SENTENCE_GENERATED'
    event_type = StringField(required=True)
    
    # Flexible field to store event-specific details
    details = DynamicField()

    meta = {
        'collection': 'interaction_logs',
        'indexes': [
            'user',
            'timestamp',
            'event_type'
        ]
    }