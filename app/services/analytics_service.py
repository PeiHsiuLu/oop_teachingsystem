from app.models.analytics import InteractionLog
from mongoengine.queryset.visitor import Q
import datetime

class AnalyticsEngine:
    """
    Provides methods for logging user interactions and generating analytical reports.
    """
    def log_event(self, user_id: str, event_type: str, details: dict):
        """
        Creates and saves a new InteractionLog document.
        """
        log_entry = InteractionLog(
            user=user_id,
            event_type=event_type,
            details=details
        )
        log_entry.save()
        return log_entry

    def generate_weakness_report(self, user_id: str, days: int = 7) -> dict:
        """
        Generates a report of words the user has struggled with recently.
        This is a simplified example using aggregation.
        """
        since_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # MongoDB Aggregation Pipeline to find words frequently marked as 'hard'
        pipeline = [
            {'$match': {'user': user_id, 'timestamp': {'$gte': since_date}, 'event_type': 'WORD_REVIEW', 'details.user_response': 'hard'}},
            {'$group': {'_id': '$details.word_id', 'hard_count': {'$sum': 1}}},
            {'$sort': {'hard_count': -1}},
            {'$limit': 10}
        ]
        
        results = InteractionLog.objects.aggregate(pipeline)
        return list(results)