from app.models.report import Report
from app.models.user import User
from app.services.level_system import LevelSystem


class ModService:
    def __init__(self):
        self.level_system = LevelSystem()

    def process_report(self, report_event):
        reporter = User.objects(id=report_event.get("reporter_id")).first()
        target_user = None

        if report_event.get("target_user_id"):
            target_user = User.objects(id=report_event.get("target_user_id")).first()

        if not reporter:
            raise ValueError("Reporter not found.")

        if not report_event.get("target_type"):
            raise ValueError("Target type is required.")

        if not report_event.get("target_id"):
            raise ValueError("Target id is required.")

        if not report_event.get("reason"):
            raise ValueError("Reason is required.")

        report = Report(
            reporter=reporter,
            target_user=target_user,
            target_type=report_event.get("target_type"),
            target_id=report_event.get("target_id"),
            reason=report_event.get("reason")
        )

        report.save()
        return report

    def apply_sanction(self, user_id, action_type):
        user = User.objects(id=user_id).first()

        if not user:
            raise ValueError("User not found.")

        if action_type == "mute":
            if hasattr(user, "credit_score"):
                user.credit_score = max(0, user.credit_score - 20)

            if hasattr(user, "xp"):
                user.xp = max(0, user.xp - 20)

            if hasattr(user, "is_muted"):
                user.is_muted = True

            user.save()
            self.level_system.update_user_level(user)

            return "User muted / credit score and XP reduced."

        if action_type == "warning":
            if hasattr(user, "credit_score"):
                user.credit_score = max(0, user.credit_score - 5)

            if hasattr(user, "xp"):
                user.xp = max(0, user.xp - 5)

            user.save()
            self.level_system.update_user_level(user)

            return "Warning applied / credit score and XP reduced."

        return "No action applied."