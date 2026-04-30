from datetime import datetime
from app.repositories.base_repository import BaseRepository

from app.models.vocabulary import VocabularyBank 

class VocabularyRepository(BaseRepository):
    def __init__(self):
        super().__init__(VocabularyBank)

    def get_user_bank(self, user_id):
        """Retrieve the vocabulary bank for a specific student."""
        return self.model.objects(user_id=user_id).first()
        
    def get_words_due_for_review(self, user_id, date=None):
        """
        Efficiently retrieve words due for review for a specific user
        using a database-level aggregation pipeline.
        """
        target_date = date or datetime.utcnow()
        
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$unwind': '$list_of_words'},
            {'$match': {'list_of_words.next_review_date': {'$lte': target_date}}},
            {'$replaceRoot': {'newRoot': '$list_of_words'}}
        ]
        
        # The aggregation returns raw dicts, so we convert them back to Word objects
        word_dicts = list(self.model.objects.aggregate(pipeline))
        
        # Note: This requires the Word model to be imported
        from app.models.vocabulary import Word
        return [Word(**data) for data in word_dicts]