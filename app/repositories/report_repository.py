from app.repositories.base_repository import BaseRepository
from app.models.report import Report


class ReportRepository(BaseRepository):
    def __init__(self):
        super().__init__(Report)

    def get_pending_reports(self):
        return Report.objects(status="pending").order_by("-created_at")

    def archive_report(self, report_id):
        report = self.find_by_id(report_id)
        if not report:
            return False
        report.archive()
        return True

    def resolve_report(self, report_id):
        report = self.find_by_id(report_id)
        if not report:
            return False
        report.resolve()
        return True