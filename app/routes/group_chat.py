from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models.team import StudyGroup
from app.models.group_chat import GroupChat, ChatMessage
from app.models.report import Report
from app.services.achievement_service import AchievementService


achievement_service = AchievementService()

group_chat_bp = Blueprint(
    "group_chat",
    __name__,
    url_prefix="/group-chat"
)


def is_ajax_request():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def user_is_muted(user):
    """
    Safely check whether a user is muted.

    This prevents AttributeError if Student.is_muted() has not been added yet.
    """
    if not user:
        return False

    if hasattr(user, "is_muted") and callable(user.is_muted):
        return user.is_muted()

    credit_score = getattr(user, "credit_score", 100)

    if credit_score is None:
        credit_score = 100

    return credit_score <= 0


def format_message_time(message):
    if not message or not getattr(message, "created_at", None):
        return ""

    return message.created_at.strftime("%Y-%m-%d %H:%M")


def get_reported_message_ids(user, messages):
    """
    Return message ids that current user has already reported.

    重新整理頁面後，用這個資料讓已檢舉過的訊息顯示 Reported｜已檢舉。
    """
    reported_message_ids = set()

    if not user or not messages:
        return reported_message_ids

    message_ids = [str(message.id) for message in messages]

    reports = Report.objects(
        reporter=user,
        target_type="chat_message",
        target_id__in=message_ids
    )

    for report in reports:
        if report.target_id:
            reported_message_ids.add(str(report.target_id))

    return reported_message_ids


@group_chat_bp.route("/<group_id>", methods=["GET", "POST"])
@login_required
def chat_room(group_id):
    group = StudyGroup.objects(id=group_id).first()

    if not group:
        if is_ajax_request():
            return jsonify({
                "ok": False,
                "error": "Team not found. 找不到團隊。"
            }), 404

        flash("Team not found.", "error")
        return redirect(url_for("team.teams_dashboard"))

    is_member = any(
        str(member.id) == str(current_user.id)
        for member in group.members
    )

    if current_user.role != "admin" and not is_member:
        if is_ajax_request():
            return jsonify({
                "ok": False,
                "error": "You are not allowed to enter this chat room. 你沒有權限進入這個聊天室。"
            }), 403

        flash("You are not allowed to enter this chat room.", "error")
        return redirect(url_for("team.teams_dashboard"))

    chat = GroupChat.objects(group=group).first()

    if not chat:
        chat = GroupChat(group=group)
        chat.save()

    if request.method == "POST":
        if current_user.role == "student" and user_is_muted(current_user):
            if is_ajax_request():
                return jsonify({
                    "ok": False,
                    "error": "You are muted and cannot send messages. 你目前被禁言，無法傳送訊息。"
                }), 403

            flash("You are muted and cannot send messages.", "error")
            return redirect(url_for("group_chat.chat_room", group_id=group.id))

        content = request.form.get("content", "").strip()

        if not content:
            if is_ajax_request():
                return jsonify({
                    "ok": False,
                    "error": "Message cannot be empty. 訊息不能是空白。"
                }), 400

            flash("Message cannot be empty.", "error")
            return redirect(url_for("group_chat.chat_room", group_id=group.id))

        message = ChatMessage(
            chat=chat,
            sender=current_user._get_current_object(),
            message_type="text",
            content=content
        )
        message.save()

        try:
            achievement_service.unlock_badge(
                current_user._get_current_object(),
                "first_message"
            )
        except Exception as e:
            print(f"[Group Chat Achievement] Failed to unlock first_message: {e}")

        if is_ajax_request():
            return jsonify({
                "ok": True,
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender_id": str(message.sender.id),
                    "sender_username": message.sender.username,
                    "created_at": format_message_time(message),
                    "is_mine": True
                }
            })

        return redirect(url_for("group_chat.chat_room", group_id=group.id))

    messages = ChatMessage.objects(chat=chat).order_by("created_at")
    reported_message_ids = get_reported_message_ids(
        current_user._get_current_object(),
        messages
    )

    return render_template(
        "group_chat.html",
        group=group,
        chat=chat,
        messages=messages,
        reported_message_ids=reported_message_ids
    )