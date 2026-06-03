from app.models.report import Report
from app.models.user import User

try:
    from app.services.level_system import LevelSystem
except Exception:
    LevelSystem = None


class ModService:
    def __init__(self):
        self.level_system = None

        if LevelSystem:
            try:
                self.level_system = LevelSystem()
            except Exception as e:
                print(f"[ReportService] LevelSystem init failed: {e}")
                self.level_system = None

    def process_report(self, report_event):
        """
        Create a report.

        Rules:
        1. Reporter must exist.
        2. Target type, target id, and reason are required.
        3. User cannot report themselves.
        4. Same reporter cannot report the same target again,
           no matter whether the previous report is pending, resolved, or archived.

        建立檢舉案件。

        規則：
        1. 檢舉者必須存在。
        2. 檢舉類型、目標 ID、原因都必須存在。
        3. 使用者不能檢舉自己。
        4. 同一位使用者不能重複檢舉同一個目標。
        """

        reporter_id = report_event.get("reporter_id")
        target_user_id = report_event.get("target_user_id")
        target_type = (report_event.get("target_type") or "").strip()
        target_id = (report_event.get("target_id") or "").strip()
        reason = (report_event.get("reason") or "").strip()

        reporter = User.objects(id=reporter_id).first()
        target_user = None

        if target_user_id:
            target_user = User.objects(id=target_user_id).first()

        if not reporter:
            raise ValueError("Reporter not found. 找不到檢舉者。")

        if not target_type:
            raise ValueError("Target type is required. 缺少檢舉類型。")

        if not target_id:
            raise ValueError("Target ID is required. 缺少檢舉目標 ID。")

        if not reason:
            raise ValueError("Reason is required. 請填寫檢舉原因。")

        if target_user and str(reporter.id) == str(target_user.id):
            raise ValueError("You cannot report yourself. 不能檢舉自己。")

        duplicate_report = Report.objects(
            reporter=reporter,
            target_type=target_type,
            target_id=target_id
        ).first()

        if duplicate_report:
            raise ValueError("You have already reported this item. 你已經檢舉過這個項目。")

        report = Report(
            reporter=reporter,
            target_user=target_user,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            status="pending"
        )

        report.save()
        return report

    def apply_sanction(self, user_id, action_type, reason=""):
        """
        Apply moderation sanction to a student.

        warning:
        - credit_score -5
        - xp -5
        - write sanction notice

        mute:
        - credit_score = 0
        - xp -20
        - write sanction notice
        - credit_score <= 0 means muted
        """

        user = User.objects(id=user_id).first()

        if not user:
            raise ValueError("User not found. 找不到使用者。")

        action_type = (action_type or "").lower().strip()
        reason = (reason or "").strip()

        if getattr(user, "role", "") != "student":
            raise ValueError("Only students can receive sanctions. 只有學生可以被懲處。")

        current_credit_score = getattr(user, "credit_score", 100)

        if current_credit_score is None:
            current_credit_score = 100

        current_xp = getattr(user, "xp", 0)

        if current_xp is None:
            current_xp = 0

        if action_type == "warning":
            user.credit_score = max(0, int(current_credit_score) - 5)
            user.xp = max(0, int(current_xp) - 5)

            warning_notice = (
                "You received a warning from the administrator. "
                "Your credit score decreased by 5 points and your XP decreased by 5 points. "
                "你收到管理員警告，信用分數扣除 5 分，XP 扣除 5 點。"
            )

            if hasattr(user, "set_sanction_notice"):
                user.set_sanction_notice(
                    sanction_type="warning",
                    notice=warning_notice,
                    reason=reason
                )
            else:
                user.save()

            self._safe_update_level(user)

            return (
                "Warning applied. Credit score -5 and XP -5. "
                "已套用警告，信用分數 -5，XP -5。"
            )

        if action_type == "mute":
            user.credit_score = 0
            user.xp = max(0, int(current_xp) - 20)

            mute_notice = (
                "You have been muted by the administrator. "
                "Your credit score was set to 0 and your XP decreased by 20 points. "
                "You cannot send messages while muted. "
                "你已被管理員禁言，信用分數已設為 0，XP 扣除 20 點。"
                "禁言期間你無法傳送聊天室訊息。"
            )

            if hasattr(user, "set_sanction_notice"):
                user.set_sanction_notice(
                    sanction_type="mute",
                    notice=mute_notice,
                    reason=reason
                )
            else:
                user.save()

            self._safe_update_level(user)

            return (
                "User muted. Credit score set to 0 and XP -20. "
                "已禁言使用者，信用分數設為 0，XP -20。"
            )

        raise ValueError("Invalid sanction type. 無效的懲處類型。")

    def _safe_update_level(self, user):
        if not self.level_system:
            return

        try:
            self.level_system.update_user_level(user)
        except Exception as e:
            print(f"[ReportService] Level update failed: {e}")