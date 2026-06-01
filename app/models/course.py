from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    ListField,
    ReferenceField,
    EmbeddedDocumentField
)
from app.services.unlock_rules import LevelRule, ScoreRule

class Unit(Document):
    title = StringField(required=True)
    content = StringField() 
    unit_type = StringField(default="text") # e.g., 'text', 'video', 'quiz'
    
    # New method to help the UI
    def get_template(self):
        return f"units/{self.unit_type}.html"
class QuizQuestion(EmbeddedDocument):
    """
    Vocabulary quiz question for each chapter.
    """

    question = StringField(required=True)
    options = ListField(StringField(), required=True)
    answer = StringField(required=True)
    target_word = StringField(default="")
    explanation = StringField(default="")
class Chapter(Document):
    quiz_questions = ListField(EmbeddedDocumentField(QuizQuestion))
    title = StringField(required=True)
    units = ListField(ReferenceField(Unit)) # Chapter is composed of many Units
    unlock_rule_type = StringField() # e.g., "level" or "score"
    unlock_threshold = IntField()    # e.g., 5 or 80
    meta = {
        'strict': False  # This tells MongoEngine: "Ignore fields in the DB that aren't in the class"
    }

    def is_unlocked(self, user):
        # We need to make sure we don't crash if an Admin visits the page
        # (Admins might not have 'level' or 'credit_score')
        if hasattr(user, 'level') == False:
            return True # Admins can see everything

        rules = {
            "level": LevelRule(self.unlock_threshold or 0),
            "score": ScoreRule(self.unlock_threshold or 0)
        }
        rule = rules.get(self.unlock_rule_type)
        
        if not rule: 
            return True 
        return rule.evaluate(user, self)

    def get_rule_description(self):
        if self.unlock_rule_type == "none":
            return "No requirements"
        return f"User {self.unlock_rule_type.capitalize()} {self.unlock_threshold}"

class LearningPath(Document):
    path_name = StringField(required=True)
    chapters = ListField(ReferenceField(Chapter)) # Path is composed of many chapters