from mongoengine import Document, StringField, ListField, EmbeddedDocument, EmbeddedDocumentField

class DialogueOption(EmbeddedDocument):
    """Represents a choice a user can make in a dialogue."""
    text = StringField(required=True)
    # The ID of the DialogueNode to go to next
    next_node_id = StringField(required=True) 

class DialogueNode(Document):
    """
    Represents a single point in a conversation tree.
    A collection of nodes with the same scenario_id forms a complete dialogue scenario.
    """
    scenario_id = StringField(required=True) # e.g., "restaurant_ordering"
    node_id = StringField(required=True) # e.g., "start", "ask_for_menu", "order_drink"
    speaker = StringField(default="system") # Who is speaking, "system" or "user"
    text = StringField(required=True) # The dialogue text
    options = ListField(EmbeddedDocumentField(DialogueOption)) # User's choices from this node

    meta = {
        'collection': 'dialogue_nodes',
        'indexes': [
            # Create a compound index for efficient lookup of a specific node in a scenario
            {'fields': ('scenario_id', 'node_id'), 'unique': True}
        ]
    }