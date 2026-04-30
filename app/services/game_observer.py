from app.models.user import Student

class GamificationObserver:
    """
    Implements the Observer Pattern for Gamification (Use Case 6).
    Listens for completed learning tasks and automatically awards XP/Badges.
    """
    @staticmethod
    def on_task_completed(user_id: str, task_type: str, score: int = 0):
        student = Student.objects(id=user_id).first()
        if not student:
            return
            
        xp_to_add = 0
        if task_type == 'vocabulary_review':
            xp_to_add = 5 + (score * 2)  # Earn up to 15 XP for a perfect rating
        elif task_type == 'dialogue_finished':
            xp_to_add = 20 + int(score * 0.5) # E.g., 85 score = +62 XP
            
        if hasattr(student, 'add_xp'):
            student.add_xp(xp_to_add)
        else:
            # Fallback if add_xp isn't fully implemented on the model yet
            student.xp = getattr(student, 'xp', 0) + xp_to_add
            student.save()