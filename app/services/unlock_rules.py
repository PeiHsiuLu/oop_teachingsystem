from abc import ABC, abstractmethod

class UnlockRule(ABC):
    @abstractmethod
    def evaluate(self, user, unit_or_chapter):
        pass

# Concrete Rule: Level-based unlocking
class LevelRule(UnlockRule):
    def __init__(self, required_level):
        self.required_level = required_level
        
    def evaluate(self, user, item):
        return user.level >= self.required_level

# Concrete Rule: Score-based unlocking
class ScoreRule(UnlockRule):
    def __init__(self, min_score):
        self.min_score = min_score
        
    def evaluate(self, user, item):
        return user.credit_score >= self.min_score