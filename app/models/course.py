from mongoengine import Document, StringField, ReferenceField, ListField, IntField
from app.services.unlock_rules import LevelRule, ScoreRule

class Unit(Document):
    title = StringField(required=True)
    content = StringField() # Or link to a static asset

class Chapter(Document):
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

class LearningPath(Document):
    path_name = StringField(required=True)
    chapters = ListField(ReferenceField(Chapter)) # Path is composed of many chapters