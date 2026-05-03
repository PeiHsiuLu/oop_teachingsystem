from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.team import StudyGroup
from app.models.group_chat import GroupChat, ChatMessage


group_chat_bp = Blueprint(
    "group_chat",
    __name__,
    url_prefix="/group-chat"
)


@group_chat_bp.route("/<group_id>", methods=["GET", "POST"])
@login_required
def chat_room(group_id):
    group = StudyGroup.objects(id=group_id).first()

    if not group:
        flash("Team not found.", "error")
        return redirect(url_for("team.teams_dashboard"))

    is_member = any(
        str(member.id) == str(current_user.id)
        for member in group.members
    )

    if current_user.role != "admin" and not is_member:
        flash("You are not allowed to enter this chat room.", "error")
        return redirect(url_for("team.teams_dashboard"))

    chat = GroupChat.objects(group=group).first()

    if not chat:
        chat = GroupChat(group=group)
        chat.save()

    if request.method == "POST":
        content = request.form.get("content")

        if not content or content.strip() == "":
            flash("Message cannot be empty.", "error")
            return redirect(url_for("group_chat.chat_room", group_id=group.id))

        message = ChatMessage(
            chat=chat,
            sender=current_user._get_current_object(),
            message_type="text",
            content=content.strip()
        )

        message.save()

        return redirect(url_for("group_chat.chat_room", group_id=group.id))

    messages = ChatMessage.objects(chat=chat).order_by("created_at")

    return render_template(
        "group_chat.html",
        group=group,
        chat=chat,
        messages=messages
    )