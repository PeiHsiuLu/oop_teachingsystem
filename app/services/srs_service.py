from abc import ABC, abstractmethod
import datetime
from app.models.word import ReviewItem, Word
from app.repositories.word_repository import WordRepository

# --- Step 1: Define the Strategy Interface (as an Abstract Base Class) ---
class SRSAlgorithmStrategy(ABC):
    """
    The interface for any Spaced Repetition System algorithm.
    It defines how to update a review item based on user performance.
    """
    @abstractmethod
    def process_review(self, review_item: ReviewItem, quality: int) -> ReviewItem:
        """
        Updates the review_item's SRS fields (due_date, interval, ease_factor)
        based on the quality of the user's answer.
        :param review_item: The ReviewItem document to update.
        :param quality: An integer from 0-5 representing recall quality.
                        (e.g., 0: complete blackout, 3: correct but with difficulty, 5: perfect recall)
        :return: The updated ReviewItem.
        """
        pass

# --- Step 2: Define Concrete Strategy Implementations ---
class SuperMemo2Strategy(SRSAlgorithmStrategy):
    """
    An implementation of a simplified SM-2 algorithm.
    This is a classic and effective SRS algorithm.
    """
    def process_review(self, review_item: ReviewItem, quality: int) -> ReviewItem:
        review_item.review_count += 1
        review_item.last_reviewed = datetime.datetime.utcnow()

        if quality < 3:
            # If recall was poor, reset the interval
            review_item.interval = 1
            review_item.review_count = 1 # Treat as a new learning item
        else:
            # If recall was good, calculate the new interval
            if review_item.review_count == 1:
                review_item.interval = 1
            elif review_item.review_count == 2:
                review_item.interval = 6
            else:
                review_item.interval = round(review_item.interval * review_item.ease_factor)

            # Update the ease factor
            new_ease = review_item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            review_item.ease_factor = max(1.3, new_ease) # Ease factor should not go below 1.3

        review_item.due_date = datetime.datetime.utcnow() + datetime.timedelta(days=review_item.interval)
        return review_item

# --- Step 3: Create the Context Class (SRSManager) that uses a Strategy ---
class SRSManager:
    """
    Manages the student's review schedule using a configurable SRS algorithm.
    This class doesn't know the details of the algorithm, only that it can process a review.
    """
    def __init__(self, strategy: SRSAlgorithmStrategy, word_repository: WordRepository):
        self._strategy = strategy
        self.word_repo = word_repository

    def get_words_for_review(self, user_id: str, limit: int = 10):
        """
        Gets a list of words that are due for review for a given user.
        It prioritizes due items, then falls back to new, unreviewed words.
        """
        now = datetime.datetime.utcnow()
        # Find items that are due
        due_items = ReviewItem.objects(user=user_id, due_date__lte=now).order_by('due_date').limit(limit)
        
        if due_items.count() < limit:
            # If not enough due items, supplement with new words
            num_new_words_needed = limit - due_items.count()
            new_words = self.word_repo.get_unreviewed_words_for_user(user_id, limit=num_new_words_needed)
            
            # We return a mix of ReviewItem objects and Word objects
            # The route handler will need to format them consistently
            return list(due_items) + list(new_words)
            
        return list(due_items)

    def process_review_result(self, user_id: str, word_id: str, quality: int) -> ReviewItem:
        """
        Processes the result of a single word review.
        It finds or creates a ReviewItem and uses the configured strategy to update it.
        """
        review_item = self.word_repo.get_review_item(user_id, word_id)

        if not review_item:
            # This is the first time the user is seeing this word
            word = self.word_repo.find_by_id(word_id)
            if not word:
                raise ValueError(f"Word with ID {word_id} not found.")
            review_item = ReviewItem(user=user_id, word=word)

        # Delegate the complex calculation to the strategy object
        updated_item = self._strategy.process_review(review_item, quality)
        
        updated_item.save()
        return updated_item