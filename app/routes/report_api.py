from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.report_service import ModService
from app.models.report import Report
from app.utils.decorators import role_required

report_bp = Blueprint("report", __name__)
mod_service = ModService()


@report_bp.route("/api/reports/create", methods=["POST"])
@login_required
def create_report():
    data = request.form if request.form else request.json

    report_event = {
        "reporter_id": str(current_user.id),
        "target_user_id": data.get("target_user_id"),
        "target_type": data.get("target_type"),
        "target_id": data.get("target_id"),
        "reason": data.get("reason")
    }

    try:
        report = mod_service.process_report(report_event)
        flash("Report submitted successfully.", "success")
        return redirect(url_for("main.index"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@report_bp.route("/admin/reports", methods=["GET"])
@login_required
@role_required("admin")
def admin_reports():
    reports = Report.objects(status="pending").order_by("-created_at")
    return render_template("admin_reports.html", reports=reports)


@report_bp.route("/api/reports/<report_id>/resolve", methods=["POST"])
@login_required
@role_required("admin")
def resolve_report(report_id):
    report = Report.objects(id=report_id).first()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    report.resolve()
    flash("Report resolved.", "success")
    return redirect(url_for("report.admin_reports"))


@report_bp.route("/api/reports/<report_id>/archive", methods=["POST"])
@login_required
@role_required("admin")
def archive_report(report_id):
    report = Report.objects(id=report_id).first()
    if not report:
        return jsonify({"error": "Report not found"}), 404

    report.archive()
    flash("Report archived.", "success")
    return redirect(url_for("report.admin_reports"))

@report_bp.route("/api/reports/sanction/<user_id>", methods=["POST"])
@login_required
@role_required("admin")
def apply_sanction(user_id):
    action_type = request.form.get("action_type")
    try:
        message = mod_service.apply_sanction(user_id, action_type)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("report.admin_reports"))