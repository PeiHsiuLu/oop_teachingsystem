from abc import ABC, abstractmethod
import datetime

from app.models.word import ReviewItem
from app.repositories.word_repository import WordRepository


class SRSAlgorithmStrategy(ABC):
    """
    Interface for spaced repetition algorithms.
    """

    @abstractmethod
    def process_review(self, review_item: ReviewItem, quality: int) -> ReviewItem:
        pass


class SuperMemo2Strategy(SRSAlgorithmStrategy):
    """
    Demo version of spaced repetition.

    For demo:
    Forgot = review again after 10 seconds
    Hard   = review again after 30 seconds
    Easy   = review again after 60 seconds
    """

    def process_review(self, review_item: ReviewItem, quality: int) -> ReviewItem:
        now = datetime.datetime.utcnow()

        review_item.review_count += 1
        review_item.last_reviewed = now

        if quality <= 2:
            # Forgot
            review_item.interval = 10
            review_item.ease_factor = max(1.3, review_item.ease_factor - 0.2)

        elif quality == 3:
            # Hard
            review_item.interval = 30
            review_item.ease_factor = max(1.3, review_item.ease_factor - 0.05)

        else:
            # Easy
            review_item.interval = 60
            review_item.ease_factor = review_item.ease_factor + 0.1

        # Demo version: interval means seconds.
        review_item.due_date = now + datetime.timedelta(seconds=review_item.interval)

        return review_item


class SRSManager:
    """
    Manages vocabulary review schedule.
    """

    def __init__(self, strategy: SRSAlgorithmStrategy, word_repository: WordRepository):
        self._strategy = strategy
        self.word_repo = word_repository

    def get_words_for_review(self, user_id: str, limit: int = 10):
        """
        Get due review items.

        Only words already added to ReviewItem can appear in Vocabulary Review.
        This prevents the system from pulling random words from the whole database.
        """

        now = datetime.datetime.utcnow()

        due_items = ReviewItem.objects(
            user=user_id,
            due_date__lte=now
        ).order_by("due_date").limit(limit)

        return list(due_items)

    def get_review_queue(self, user_id: str):
        """
        Get all words in the user's review queue.
        Used for displaying the review list page.
        """

        review_items = ReviewItem.objects(
            user=user_id
        ).order_by("due_date")

        return list(review_items)

    def add_word_to_review_queue(self, user_id: str, word_id: str) -> ReviewItem:
        """
        Add a word to the user's review queue.

        This method prevents duplicate review items.

        It checks:
        1. Same word_id
        2. Same word_text, such as two duplicated "umbrella" records
        """

        # 1. Check exact same word_id first
        review_item = self.word_repo.get_review_item(user_id, word_id)

        if review_item:
            return review_item

        word = self.word_repo.find_by_id(word_id)

        if not word:
            raise ValueError(f"Word with ID {word_id} not found.")

        target_word_text = word.word_text.strip().lower()

        # 2. Check whether another ReviewItem already has the same word_text
        existing_items = ReviewItem.objects(user=user_id)

        for item in existing_items:
            if not item.word:
                continue

            if not item.word.word_text:
                continue

            existing_word_text = item.word.word_text.strip().lower()

            if existing_word_text == target_word_text:
                return item

        review_item = ReviewItem(
            user=user_id,
            word=word,
            due_date=datetime.datetime.utcnow(),
            interval=0,
            ease_factor=2.5,
            review_count=0
        )

        review_item.save()
        return review_item

    def process_review_result(self, user_id: str, word_id: str, quality: int) -> ReviewItem:
        """
        Process user's review result and update next review time.
        """

        review_item = self.word_repo.get_review_item(user_id, word_id)

        if not review_item:
            review_item = self.add_word_to_review_queue(user_id, word_id)

        updated_item = self._strategy.process_review(review_item, quality)
        updated_item.save()

        return updated_item