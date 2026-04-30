from app.repositories.vocabulary_repository import VocabularyRepository
from app.models.vocabulary import Word, VocabularyBank
from app.services.game_observer import GamificationObserver

class VocabularyService:
    def __init__(self):
        self.repo = VocabularyRepository()

    def generate_dynamic_sentence(self, word: str, rules: dict = None) -> str:
        """
        UC3_2: 動態生成情境例句 (Dynamic Sentence Generation).
        In a full implementation, this would connect to an LLM or a Sentence Database
        using the rules defined by the Admin.
        """
        # Placeholder for AI logic
        return f"This is an auto-generated example sentence demonstrating the use of '{word}'."

    def process_review(self, user_id: str, word_str: str, performance_rating: int) -> bool:
        """
        UC3_1: 進行間隔重複複習 (Process Spaced Repetition Review).
        Updates the interval based on the student's rating and saves it.
        """
        # Find the specific word to update directly in the database
        bank = VocabularyBank.objects(user_id=user_id, list_of_words__word=word_str).first()
        if not bank:
            return False # User or word not found
        
        # Create a temporary Word object to calculate the new SRS values
        temp_word = next((w for w in bank.list_of_words if w.word == word_str), None)
        temp_word.calculate_next_interval(performance_rating)
        
        # Atomically update only the specific word in the database
        result = VocabularyBank.objects(user_id=user_id, list_of_words__word=word_str).update_one(
            set__list_of_words__S__ease_factor=temp_word.ease_factor,
            set__list_of_words__S__interval=temp_word.interval,
            set__list_of_words__S__next_review_date=temp_word.next_review_date,
            set__list_of_words__S__last_reviewed=temp_word.last_reviewed
        )
        
        GamificationObserver.on_task_completed(user_id, 'vocabulary_review', performance_rating)
        return result == 1