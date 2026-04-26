from mongoengine import Document, StringField, ReferenceField, ListField, IntField

class Unit(Document):
    title = StringField(required=True)
    content = StringField() # Or link to a static asset

class Chapter(Document):
    title = StringField(required=True)
    units = ListField(ReferenceField('Unit')) # Chapter is composed of many Units
    unlock_rule = StringField() # example: "min_score_80"

class LearningPath(Document):
    path_name = StringField(required=True)
    chapters = ListField(ReferenceField('Chapter')) # Path is composed of many chapters