from datetime import datetime

from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    IntField,
    BooleanField,
    DateTimeField,
    ListField,
    ReferenceField,
    EmbeddedDocumentField
)


class Unit(Document):
    """
    A lesson unit.

    Unit should only store lesson content.
    Vocabulary quiz questions should be stored in Chapter.quiz_questions.
    """

    title = StringField(required=True)
    content = StringField(default="")

    meta = {
        "collection": "unit",
        "strict": False
    }


class QuizQuestion(EmbeddedDocument):
    """
    A vocabulary multiple-choice question for a Chapter.

    Each Chapter should have exactly 5 complete questions to become Quiz Ready.
    """

    question = StringField(default="")
    options = ListField(StringField(), default=list)
    answer = StringField(default="")
    target_word = StringField(default="")
    explanation = StringField(default="")

    def is_complete(self):
        """
        A question is complete only when:
        1. question is not empty
        2. exactly 4 options
        3. every option is not empty
        4. answer is not empty
        5. answer exactly matches one of the options
        6. target_word is not empty
        7. explanation is not empty
        """

        if not self.question or not self.question.strip():
            return False

        if not self.options or len(self.options) != 4:
            return False

        cleaned_options = []

        for option in self.options:
            if not option or not option.strip():
                return False

            cleaned_options.append(option.strip())

        if not self.answer or not self.answer.strip():
            return False

        if self.answer.strip() not in cleaned_options:
            return False

        if not self.target_word or not self.target_word.strip():
            return False

        if not self.explanation or not self.explanation.strip():
            return False

        return True


class UnlockRule(EmbeddedDocument):
    """
    A single unlock rule for a Chapter.

    Supported rule_type:
    - none
    - level
    - score
    - cefr
    """

    rule_type = StringField(default="none")
    value = StringField(default="")

    def get_description(self):
        if self.rule_type == "none":
            return "No requirement"

        if self.rule_type == "level":
            return f"Level >= {self.value}"

        if self.rule_type == "score":
            return f"Quiz Score >= {self.value}"

        if self.rule_type == "cefr":
            return f"CEFR >= {self.value}"

        return "Unknown requirement"


class Chapter(Document):
    """
    A chapter contains several units and one vocabulary quiz.

    Quiz design:
    - Admin can save quiz as draft.
    - Only when all 5 questions are complete will it be Quiz Ready.
    """

    title = StringField(required=True)

    units = ListField(ReferenceField(Unit), default=list)

    # Legacy single-rule fields.
    # Keep these to avoid breaking old data.
    unlock_rule_type = StringField(default="none")
    unlock_threshold = IntField(default=0)

    # New multi-rule system.
    unlock_rules = ListField(EmbeddedDocumentField(UnlockRule), default=list)

    # Chapter vocabulary quiz.
    quiz_questions = ListField(EmbeddedDocumentField(QuizQuestion), default=list)

    meta = {
        "collection": "chapter",
        "strict": False
    }

    def is_quiz_ready(self):
        """
        Quiz is ready only when there are exactly 5 complete questions.
        """

        if not self.quiz_questions:
            return False

        if len(self.quiz_questions) != 5:
            return False

        for question in self.quiz_questions:
            if not question.is_complete():
                return False

        return True

    def get_quiz_status_text(self):
        if self.is_quiz_ready():
            return "Quiz Ready"

        return "Quiz Draft"

    def get_rule_description(self):
        """
        Display unlock rule description.

        Supports both:
        1. new multi-rule system: unlock_rules
        2. old legacy system: unlock_rule_type / unlock_threshold
        """

        if self.unlock_rules and len(self.unlock_rules) > 0:
            descriptions = []

            for rule in self.unlock_rules:
                if rule.rule_type and rule.rule_type != "none":
                    descriptions.append(rule.get_description())

            if descriptions:
                return " + ".join(descriptions)

        # Legacy fallback.
        if self.unlock_rule_type == "none":
            return "No requirement"

        if self.unlock_rule_type == "level":
            return f"Level >= {self.unlock_threshold}"

        if self.unlock_rule_type == "score":
            return f"Score >= {self.unlock_threshold}"

        if self.unlock_rule_type == "cefr":
            return f"CEFR >= {self.unlock_threshold}"

        return "Unknown requirement"

    def cefr_to_rank(self, cefr_level):
        levels = {
            "A1": 1,
            "A2": 2,
            "B1": 3,
            "B2": 4,
            "C1": 5,
            "C2": 6
        }

        return levels.get(str(cefr_level).upper(), 1)

    def get_best_quiz_score_for_user(self, user):
        """
        Get the user's best score for this chapter.

        If there is no attempt, return 0.
        """

        if not user:
            return 0

        try:
            best_attempt = ChapterQuizAttempt.objects(
                student=user,
                chapter=self
            ).order_by("-score").first()

            if best_attempt:
                return best_attempt.score

        except Exception:
            return 0

        return 0

    def check_single_rule(self, user, rule):
        """
        Check one UnlockRule.
        """

        if not rule:
            return True

        rule_type = rule.rule_type or "none"
        value = rule.value or ""

        if rule_type == "none":
            return True

        if rule_type == "level":
            try:
                required_level = int(value)
            except ValueError:
                required_level = 0

            user_level = getattr(user, "level", 1)
            return user_level >= required_level

        if rule_type == "score":
            try:
                required_score = int(value)
            except ValueError:
                required_score = 0

            best_score = self.get_best_quiz_score_for_user(user)
            return best_score >= required_score

        if rule_type == "cefr":
            user_cefr = getattr(user, "cefr_level", "A1")
            return self.cefr_to_rank(user_cefr) >= self.cefr_to_rank(value)

        return True

    def is_unlocked(self, user):
        """
        Determine whether a chapter is unlocked.

        Priority:
        1. If unlock_rules exists, all rules must pass.
        2. Otherwise fallback to old unlock_rule_type / unlock_threshold.
        """

        if not user:
            return False

        # New multi-rule system.
        if self.unlock_rules and len(self.unlock_rules) > 0:
            for rule in self.unlock_rules:
                if not self.check_single_rule(user, rule):
                    return False

            return True

        # Legacy fallback.
        if self.unlock_rule_type == "none":
            return True

        if self.unlock_rule_type == "level":
            user_level = getattr(user, "level", 1)
            return user_level >= self.unlock_threshold

        if self.unlock_rule_type == "score":
            best_score = self.get_best_quiz_score_for_user(user)
            return best_score >= self.unlock_threshold

        if self.unlock_rule_type == "cefr":
            user_cefr = getattr(user, "cefr_level", "A1")
            return self.cefr_to_rank(user_cefr) >= self.cefr_to_rank(str(self.unlock_threshold))

        return True


class LearningPath(Document):
    """
    A learning path contains chapters.

    Old templates sometimes use path.path_name.
    Some newer code may use path.name.
    To support both, keep path_name as the real field and provide a name property.
    """

    path_name = StringField(required=True)
    chapters = ListField(ReferenceField(Chapter), default=list)

    meta = {
        "collection": "learning_path",
        "strict": False
    }

    @property
    def name(self):
        return self.path_name

    @name.setter
    def name(self, value):
        self.path_name = value


class QuizAnswerRecord(EmbeddedDocument):
    """
    Record one answer in a chapter vocabulary quiz attempt.
    """

    question = StringField(default="")
    target_word = StringField(default="")
    user_answer = StringField(default="")
    correct_answer = StringField(default="")
    is_correct = BooleanField(default=False)
    explanation = StringField(default="")


class ChapterQuizAttempt(Document):
    """
    Record each time a student takes a chapter vocabulary quiz.

    This allows:
    1. repeated quiz attempts
    2. quiz history
    3. best score unlock rule
    4. reviewing previous answers
    """

    student = ReferenceField("Student", required=True)
    chapter = ReferenceField(Chapter, required=True)

    score = IntField(default=0)
    correct_count = IntField(default=0)
    total_questions = IntField(default=5)

    answers = ListField(EmbeddedDocumentField(QuizAnswerRecord), default=list)

    xp_gained = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "chapter_quiz_attempts",
        "ordering": ["-created_at"],
        "strict": False
    }


class UnitCompletion(Document):
    """
    Record that a student has completed/read a unit.

    Current rule:
    Entering a Unit page means the unit is completed.
    """

    student = ReferenceField("Student", required=True)
    unit = ReferenceField(Unit, required=True)
    chapter = ReferenceField(Chapter, required=True)

    completed_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "unit_completions",
        "indexes": [
            "student",
            "unit",
            "chapter"
        ],
        "ordering": ["-completed_at"],
        "strict": False
    }