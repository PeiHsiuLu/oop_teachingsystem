from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.report_service import ModService
from app.models.report import Report
from app.models.group_chat import ChatMessage
from app.utils.decorators import role_required


report_bp = Blueprint("report", __name__)
mod_service = ModService()


def is_ajax_request():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def get_request_data():
    if request.form:
        return request.form

    json_data = request.get_json(silent=True)

    if json_data:
        return json_data

    return {}


def get_status_label(status):
    status = (status or "pending").lower()

    labels = {
        "pending": "Pending｜待處理",
        "resolved": "Resolved｜已處理",
        "archived": "Archived｜已封存"
    }

    return labels.get(status, status)


def get_action_label(action_taken):
    action_taken = (action_taken or "").lower()

    labels = {
        "resolved": "Resolved only｜僅標記處理",
        "archived": "Archived｜封存",
        "warning": "Warning｜警告",
        "mute": "Mute｜禁言"
    }

    return labels.get(action_taken, "No action yet｜尚未處理")


def get_target_preview(report):
    target_type = (report.target_type or "").strip()
    target_id = (report.target_id or "").strip()

    if not target_id:
        return "No target ID. 沒有目標 ID。"

    if target_type == "chat_message":
        try:
            message = ChatMessage.objects(id=target_id).first()

            if not message:
                return "Message not found. 找不到該訊息，可能已被刪除。"

            content = message.content or ""

            if len(content) > 160:
                content = content[:160] + "..."

            return content or "Empty message. 空白訊息。"

        except Exception as e:
            print(f"[Report] Failed to load chat message preview: {e}")
            return "Unable to load message preview. 無法載入訊息預覽。"

    return f"Target ID: {target_id}"


def build_report_items(reports):
    items = []

    for report in reports:
        items.append({
            "report": report,
            "status_label": get_status_label(report.status),
            "action_label": get_action_label(getattr(report, "action_taken", "")),
            "target_preview": get_target_preview(report),
        })

    return items


@report_bp.route("/api/reports/create", methods=["POST"])
@login_required
def create_report():
    data = get_request_data()

    report_event = {
        "reporter_id": str(current_user.id),
        "target_user_id": data.get("target_user_id"),
        "target_type": data.get("target_type"),
        "target_id": data.get("target_id"),
        "reason": data.get("reason")
    }

    try:
        mod_service.process_report(report_event)

        if is_ajax_request():
            return jsonify({
                "ok": True,
                "message": "Report submitted successfully. 檢舉已送出。"
            }), 200

        flash("Report submitted successfully. 檢舉已送出。", "success")
        return redirect(request.referrer or url_for("main.index"))

    except ValueError as e:
        if is_ajax_request():
            return jsonify({
                "ok": False,
                "error": str(e)
            }), 400

        flash(str(e), "error")
        return redirect(request.referrer or url_for("main.index"))


@report_bp.route("/admin/reports", methods=["GET"])
@login_required
@role_required("admin")
def admin_reports():
    status_filter = (request.args.get("status") or "pending").lower().strip()

    if status_filter not in ["pending", "resolved", "archived", "all"]:
        status_filter = "pending"

    if status_filter == "all":
        reports = Report.objects.order_by("-created_at")
    else:
        reports = Report.objects(status=status_filter).order_by("-created_at")

    report_counts = {
        "pending": Report.objects(status="pending").count(),
        "resolved": Report.objects(status="resolved").count(),
        "archived": Report.objects(status="archived").count(),
        "all": Report.objects.count()
    }

    report_items = build_report_items(reports)

    return render_template(
        "admin_reports.html",
        report_items=report_items,
        reports=reports,
        report_counts=report_counts,
        status_filter=status_filter
    )


@report_bp.route("/api/reports/<report_id>/resolve", methods=["POST"])
@login_required
@role_required("admin")
def resolve_report(report_id):
    report = Report.objects(id=report_id).first()

    if not report:
        flash("Report not found. 找不到檢舉案件。", "error")
        return redirect(url_for("report.admin_reports"))

    report.resolve(
        handled_by=current_user._get_current_object(),
        action_taken="resolved"
    )

    flash("Report resolved. 檢舉已標記為處理完成。", "success")
    return redirect(url_for("report.admin_reports", status="pending"))


@report_bp.route("/api/reports/<report_id>/archive", methods=["POST"])
@login_required
@role_required("admin")
def archive_report(report_id):
    report = Report.objects(id=report_id).first()

    if not report:
        flash("Report not found. 找不到檢舉案件。", "error")
        return redirect(url_for("report.admin_reports"))

    report.archive(
        handled_by=current_user._get_current_object()
    )

    flash("Report archived. 檢舉已封存。", "success")
    return redirect(url_for("report.admin_reports", status="pending"))


@report_bp.route("/api/reports/sanction/<user_id>", methods=["POST"])
@login_required
@role_required("admin")
def apply_sanction(user_id):
    action_type = (request.form.get("action_type") or "").lower().strip()
    report_id = request.form.get("report_id")

    try:
        message = mod_service.apply_sanction(user_id, action_type)

        if report_id:
            report = Report.objects(id=report_id).first()

            if report:
                report.apply_action(
                    handled_by=current_user._get_current_object(),
                    action_taken=action_type
                )

        flash(message, "success")

    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("report.admin_reports", status="pending"))