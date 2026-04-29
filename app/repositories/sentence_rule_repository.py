from app.models.word import SentenceGeneratingRule
from app.repositories.base_repository import BaseRepository

class SentenceGeneratingRuleRepository(BaseRepository):
    """Repository for managing SentenceGeneratingRule data."""
    def __init__(self):
        super().__init__(SentenceGeneratingRule)

    def get_by_rule_name(self, rule_name):
        """Finds a sentence generation rule by its name."""
        return SentenceGeneratingRule.objects(rule_name=rule_name).first()

    def get_all(self):
        """Retrieves all sentence generation rules."""
        return SentenceGeneratingRule.objects()