import pytest
from mongoengine import connect, disconnect
import datetime

from app.models.word import ReviewItem
from app.services.srs_service import SuperMemo2Strategy

@pytest.fixture(autouse=True)
def database_connection():
    """
    A pytest fixture to set up an in-memory MongoDB connection (mongomock)
    for each test function. It automatically disconnects after the test.
    """
    connect('mongoenginetest', host='mongomock://localhost')
    yield
    disconnect()

class TestSuperMemo2Strategy:
    """
    Unit tests for the SuperMemo2Strategy class.
    These tests do not require a full repository or manager, as we are
    testing the calculation logic in isolation.
    """

    def test_process_review_first_time_correct(self):
        """
        Tests the SRS calculation for a brand new word that was answered correctly.
        """
        strategy = SuperMemo2Strategy()
        # A new item, not yet saved, with default values
        item = ReviewItem(interval=0, ease_factor=2.5, review_count=0)
        quality = 4 # A good, correct answer

        # Act
        updated_item = strategy.process_review(item, quality)

        # Assert
        assert updated_item.review_count == 1
        assert updated_item.interval == 1
        assert updated_item.ease_factor > 2.5 # Ease should increase slightly
        # Due date should be tomorrow
        assert updated_item.due_date.date() == (datetime.datetime.utcnow() + datetime.timedelta(days=1)).date()

    def test_process_review_second_time_correct(self):
        """
        Tests the SRS calculation for the second successful review.
        """
        strategy = SuperMemo2Strategy()
        # An item that has been reviewed once correctly
        item = ReviewItem(interval=1, ease_factor=2.6, review_count=1)
        quality = 5 # A perfect answer

        # Act
        updated_item = strategy.process_review(item, quality)

        # Assert
        assert updated_item.review_count == 2
        assert updated_item.interval == 6 # Interval should jump to 6 days
        assert updated_item.ease_factor > 2.6 # Ease should increase
        assert updated_item.due_date.date() == (datetime.datetime.utcnow() + datetime.timedelta(days=6)).date()

    def test_process_review_incorrect_answer_resets_interval(self):
        """
        Tests that a poor quality answer resets the review interval.
        """
        strategy = SuperMemo2Strategy()
        # An item that has been reviewed multiple times
        item = ReviewItem(interval=10, ease_factor=2.5, review_count=3)
        quality = 1 # A very poor answer

        # Act
        updated_item = strategy.process_review(item, quality)

        # Assert
        assert updated_item.review_count == 1 # Review count is reset
        assert updated_item.interval == 1 # Interval is reset to 1 day
        assert updated_item.ease_factor < 2.5 # Ease factor should decrease

    def test_process_review_ease_factor_does_not_go_below_floor(self):
        """
        Tests that the ease factor does not drop below the minimum of 1.3.
        """
        strategy = SuperMemo2Strategy()
        # An item with a low ease factor
        item = ReviewItem(interval=10, ease_factor=1.3, review_count=3)
        quality = 0 # The worst possible answer

        # Act
        updated_item = strategy.process_review(item, quality)

        # Assert
        assert updated_item.ease_factor == 1.3 # Should not go below the floor