from app.models.word import Word, ReviewItem
from app.repositories.base_repository import BaseRepository
import datetime

class WordRepository(BaseRepository):
    """Repository for managing Word and ReviewItem data."""
    def __init__(self):
        super().__init__(Word) # This repository primarily manages Word objects

    def get_by_word_text(self, word_text):
        """Finds a word by its text."""
        return Word.objects(word_text=word_text).first()

    def get_all(self):
        """Retrieves all words."""
        return Word.objects()

    # --- ReviewItem specific methods ---
    def get_review_item(self, user_id, word_id):
        """Retrieves a specific review item for a user and word."""
        return ReviewItem.objects(user=user_id, word=word_id).first()

    def get_review_items_for_user(self, user_id):
        """Retrieves all review items for a given user."""
        return ReviewItem.objects(user=user_id)

    def update_review_item(self, user_id, word_id, outcome):
        """
        Updates or creates a ReviewItem for a user and word based on review outcome.
        Simplified logic for mastery_level adjustment.
        """
        review_item = self.get_review_item(user_id, word_id)
        if not review_item:
            review_item = ReviewItem(user=user_id, word=word_id)
        
        review_item.last_reviewed = datetime.datetime.utcnow()
        review_item.review_count += 1

        # Simple mastery level adjustment based on outcome
        if outcome == 'easy':
            review_item.mastery_level = min(5, review_item.mastery_level + 1)
        elif outcome == 'hard':
            review_item.mastery_level = max(0, review_item.mastery_level - 1)
        # 'medium' outcome could keep mastery_level the same or adjust slightly

        review_item.save()
        return review_item

    def get_unreviewed_words_for_user(self, user_id, limit=10):
        """Gets words that a user has not yet reviewed."""
        reviewed_word_ids = [item.word.id for item in ReviewItem.objects(user=user_id)]
        return Word.objects(id__nin=reviewed_word_ids).limit(limit)

    def get_words_needing_review(self, user_id, limit=10):
        """
        Gets words that have been reviewed but need re-review (e.g., low mastery or old review date).
        This is a placeholder for a proper spaced repetition algorithm.
        """
        one_day_ago = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        return ReviewItem.objects(user=user_id, mastery_level__lt=3, last_reviewed__lt=one_day_ago).order_by('last_reviewed').limit(limit)