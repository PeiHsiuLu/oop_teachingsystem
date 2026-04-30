from app.models.analytics import InteractionLog
from app.models.vocabulary import VocabularyBank

class SRSManager:
    """
    Service interface for Result Analysis and Spaced Repetition (Use Case 5).
    """

    def get_weakness_report(self, user_id: str):
        """
        UC5_1: 檢視個人弱點報告. Analyzes InteractionLogs to determine student performance.
        """
        logs = InteractionLog.objects(user_id=user_id)
        total_logs = logs.count()
        
        if total_logs == 0:
            return {"status": "No Data", "message": "Complete more dialogues to generate a report."}
            
        avg_score = sum([log.correctness_score for log in logs]) / total_logs
        
        return {
            "total_interactions_completed": total_logs,
            "average_score": round(avg_score, 2),
            "overall_status": "Needs Improvement" if avg_score < 75 else "Excellent"
        }

    def schedule_review(self, user_id: str):
        """
        UC5_2: 產生下次複習策略. Finds words that are particularly difficult for the user.
        """
        bank = VocabularyBank.objects(user_id=user_id).first()
        if not bank:
            return []
            
        # Strategy: Focus on words with a low ease_factor (< 2.0)
        hard_words = [word for word in bank.list_of_words if word.ease_factor < 2.0]
        return hard_words

    def process_review_result(self, word_id: str, performance_rating: int):
        """UC5_4: 微調遺忘曲線模型. Used by Admins to globally adjust algorithm weights."""
        # Future Implementation: Global tuning of the SRS algorithm.
        pass