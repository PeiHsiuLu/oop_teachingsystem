from mongoengine import Document, StringField, ListField, DictField

class DialogueNode(Document):
    """
    Represents a single node in a scenario dialogue (Use Case 4).
    """
    node_id = StringField(required=True, unique=True)
    npc_text = StringField(required=True)
    # List of dictionaries to hold text and hidden attributes (UC4_4)
    list_of_options = ListField(DictField()) 

    def get_options(self):
        return self.list_of_options