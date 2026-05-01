from app.models.report import Report
from app.models.user import User


class ModService:
    def process_report(self, report_event):
        reporter = User.objects(id=report_event.get("reporter_id")).first()
        target_user = None

        if report_event.get("target_user_id"):
            target_user = User.objects(id=report_event.get("target_user_id")).first()

        if not reporter:
            raise ValueError("Reporter not found.")

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
            user.credit_score = max(0, user.credit_score - 20)
            user.save()
            return "User muted / credit score reduced."

        if action_type == "warning":
            user.credit_score = max(0, user.credit_score - 5)
            user.save()
            return "Warning applied."

        return "No action applied."