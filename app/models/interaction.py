from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    IntField,
    BooleanField,
    DateTimeField,
    ReferenceField,
)


class InteractionTopic(Document):
    title = StringField(required=True)
    description = StringField(default="")
    scenario_prompt = StringField(default="")

    required_level = IntField(default=0)
    required_cefr = StringField(default="A1")
    required_previous_score = IntField(default=0)

    order = IntField(default=1)
    xp_reward = IntField(default=10)

    is_active = BooleanField(default=True)

    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "interaction_topics",
        "ordering": ["order"],
        "strict": False,
    }

    def cefr_to_rank(self, cefr_level):
        levels = {
            "A1": 1,
            "A2": 2,
            "B1": 3,
            "B2": 4,
            "C1": 5,
            "C2": 6,
        }

        return levels.get(str(cefr_level).upper(), 1)

    def check_cefr_requirement(self, user):
        user_cefr = getattr(user, "cefr_level", "A1")
        return self.cefr_to_rank(user_cefr) >= self.cefr_to_rank(self.required_cefr)

    def get_requirement_text(self):
        requirements = []

        if self.required_level and self.required_level > 0:
            requirements.append(f"Level >= {self.required_level}")

        if self.required_cefr:
            requirements.append(f"CEFR >= {self.required_cefr}")

        if self.required_previous_score and self.required_previous_score > 0:
            requirements.append(f"Previous Topic Score >= {self.required_previous_score}")

        if not requirements:
            return "No requirement"

        return " + ".join(requirements)


class InteractionSession(Document):
    student = ReferenceField("Student", required=True)
    topic = ReferenceField(InteractionTopic, required=True)

    score = IntField(default=0)
    feedback = StringField(default="")
    completed = BooleanField(default=False)

    xp_gained = IntField(default=0)

    started_at = DateTimeField(default=datetime.utcnow)
    completed_at = DateTimeField()

    meta = {
        "collection": "interaction_sessions",
        "ordering": ["-started_at"],
        "strict": False,
    }


class InteractionMessage(Document):
    session = ReferenceField(InteractionSession, required=True)

    role = StringField(required=True)  # user / assistant / system
    content = StringField(required=True)

    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "interaction_messages",
        "ordering": ["created_at"],
        "strict": False,
    }