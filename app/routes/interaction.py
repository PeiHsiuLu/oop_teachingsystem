from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user

from app.models.interaction import (
    InteractionTopic,
    InteractionSession,
    InteractionMessage,
)

from app.models.course import LearningPath, ChapterQuizAttempt
from app.models.analytics import Progress
from app.services.gemini_interaction_service import GeminiInteractionService

try:
    from app.services.level_system import LevelSystem
except Exception:
    LevelSystem = None


interaction_bp = Blueprint("interaction", __name__)

gemini_service = GeminiInteractionService()

level_system = None

if LevelSystem:
    try:
        level_system = LevelSystem()
    except Exception:
        level_system = None


def safe_add_xp(user, xp_amount):
    if not user or xp_amount <= 0:
        return 0

    try:
        if hasattr(user, "add_xp"):
            user.add_xp(xp_amount)
        else:
            user.xp = getattr(user, "xp", 0) + xp_amount
            user.save()

        if level_system:
            try:
                level_system.update_user_level(user)
            except Exception:
                pass

        return xp_amount

    except Exception as e:
        print(f"[Interaction XP] Failed to add XP: {e}")
        return 0


def cefr_to_rank(cefr_level):
    levels = {
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C2": 6,
    }

    return levels.get(str(cefr_level).upper(), 1)


def get_path_display_name(path):
    if not path:
        return ""

    for field_name in ["path_name", "name", "title"]:
        value = getattr(path, field_name, None)

        if value:
            return str(value)

    return ""


def get_path1():
    for path in LearningPath.objects.all():
        path_name = get_path_display_name(path)

        if "Path 1" in path_name or "菜鳥出國" in path_name or "Travel" in path_name:
            return path

    return LearningPath.objects.first()


def get_best_chapter_score(user, chapter):
    best_attempt = ChapterQuizAttempt.objects(
        student=user,
        chapter=chapter,
    ).order_by("-score").first()

    if best_attempt:
        return best_attempt.score

    return 0


def has_completed_path1(user):
    path1 = get_path1()

    if not path1:
        return False

    chapters = list(getattr(path1, "chapters", []))

    if not chapters:
        return False

    for chapter in chapters:
        for unit in getattr(chapter, "units", []):
            completed = Progress.objects(
                student=user,
                unit=unit,
            ).first()

            if not completed:
                return False

        best_score = get_best_chapter_score(user, chapter)

        if best_score < 60:
            return False

    return True


def is_interaction_base_unlocked(user):
    user_level = getattr(user, "level", 1)

    if user_level < 5:
        return False

    if not has_completed_path1(user):
        return False

    return True


def get_unfinished_session(user, topic):
    return InteractionSession.objects(
        student=user,
        topic=topic,
        completed=False,
    ).order_by("-started_at").first()


def get_topic_sessions(user, topic, limit=20):
    return InteractionSession.objects(
        student=user,
        topic=topic,
    ).order_by("-started_at")[:limit]


def get_session_preview(session):
    latest_message = InteractionMessage.objects(
        session=session,
    ).order_by("-created_at").first()

    if not latest_message:
        return "No message yet."

    content = latest_message.content or ""

    if len(content) > 52:
        return content[:52] + "..."

    return content


def get_best_topic_score(user, topic):
    best_session = InteractionSession.objects(
        student=user,
        topic=topic,
        completed=True,
    ).order_by("-score").first()

    if best_session:
        return best_session.score

    return 0


def get_latest_topic_score(user, topic):
    latest_session = InteractionSession.objects(
        student=user,
        topic=topic,
        completed=True,
    ).order_by("-completed_at", "-started_at").first()

    if latest_session:
        return latest_session.score

    return None


def get_topic_practice_count(user, topic):
    return InteractionSession.objects(
        student=user,
        topic=topic,
        completed=True,
    ).count()


def get_previous_topic(topic):
    return InteractionTopic.objects(
        order=getattr(topic, "order", 1) - 1,
        is_active=True,
    ).first()


def is_topic_unlocked(user, topic):
    if not is_interaction_base_unlocked(user):
        return False

    user_level = getattr(user, "level", 1)

    if user_level < getattr(topic, "required_level", 0):
        return False

    user_cefr = getattr(user, "cefr_level", "A1")
    topic_cefr = getattr(topic, "required_cefr", "A1")

    if cefr_to_rank(user_cefr) < cefr_to_rank(topic_cefr):
        return False

    required_previous_score = getattr(topic, "required_previous_score", 0)

    if required_previous_score > 0:
        previous_topic = get_previous_topic(topic)

        if not previous_topic:
            return False

        previous_best_score = get_best_topic_score(user, previous_topic)

        if previous_best_score < required_previous_score:
            return False

    return True


def seed_interaction_topics():
    default_topics = [
        {
            "order": 1,
            "title": "Airport Survival Chat",
            "description": "Practice airport check-in, tickets, luggage, and boarding.",
            "scenario_prompt": "Airport check-in and boarding conversation.",
            "required_level": 5,
            "required_cefr": "A2",
            "required_previous_score": 0,
            "xp_reward": 10,
        },
        {
            "order": 2,
            "title": "Hotel Help Desk Chat",
            "description": "Practice hotel check-in, room facilities, and service requests.",
            "scenario_prompt": "Hotel front desk conversation.",
            "required_level": 6,
            "required_cefr": "A2",
            "required_previous_score": 70,
            "xp_reward": 12,
        },
        {
            "order": 3,
            "title": "Making Friends Chat",
            "description": "Practice small talk, hobbies, and making plans.",
            "scenario_prompt": "Meeting a new friend and chatting naturally.",
            "required_level": 7,
            "required_cefr": "B1",
            "required_previous_score": 70,
            "xp_reward": 14,
        },
        {
            "order": 4,
            "title": "Dining & Food Culture Chat",
            "description": "Practice ordering food, describing taste, and dining culture.",
            "scenario_prompt": "Restaurant ordering and dining conversation.",
            "required_level": 8,
            "required_cefr": "B1",
            "required_previous_score": 75,
            "xp_reward": 16,
        },
        {
            "order": 5,
            "title": "Problem Solving Abroad Chat",
            "description": "Practice solving travel problems, lost items, complaints, and help requests.",
            "scenario_prompt": "Service desk problem-solving conversation.",
            "required_level": 10,
            "required_cefr": "B2",
            "required_previous_score": 80,
            "xp_reward": 20,
        },
    ]

    for topic_data in default_topics:
        topic = InteractionTopic.objects(order=topic_data["order"]).first()

        if topic:
            continue

        InteractionTopic(**topic_data).save()


def build_topic_status(user, topic):
    persona = gemini_service.get_topic_persona(topic)
    unfinished_session = get_unfinished_session(user, topic)

    total_session_count = InteractionSession.objects(
        student=user,
        topic=topic,
    ).count()

    return {
        "unlocked": is_topic_unlocked(user, topic),
        "best_score": get_best_topic_score(user, topic),
        "latest_score": get_latest_topic_score(user, topic),
        "practice_count": get_topic_practice_count(user, topic),
        "total_session_count": total_session_count,
        "unfinished_session": unfinished_session,
        "unfinished_session_id": str(unfinished_session.id) if unfinished_session else "",
        "persona_name": persona["role_name"],
        "persona_emoji": persona["emoji"],
        "requirement_text": (
            topic.get_requirement_text()
            if hasattr(topic, "get_requirement_text")
            else f"Level >= {topic.required_level} + CEFR >= {topic.required_cefr}"
        ),
    }


@interaction_bp.route("/student/interaction")
@login_required
def interaction_topics():
    if current_user.role != "student":
        return "Unauthorized", 403

    seed_interaction_topics()

    user = current_user._get_current_object()
    topics = InteractionTopic.objects(is_active=True).order_by("order")

    base_unlocked = is_interaction_base_unlocked(user)
    topic_status = {}

    for topic in topics:
        topic_status[str(topic.id)] = build_topic_status(user, topic)

    return render_template(
        "interaction_topics.html",
        topics=topics,
        topic_status=topic_status,
        base_unlocked=base_unlocked,
        user=user,
    )


@interaction_bp.route("/student/interaction/topic/<topic_id>/history")
@login_required
def interaction_topic_history(topic_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    topic = InteractionTopic.objects.get(id=topic_id)

    persona = gemini_service.get_topic_persona(topic)

    sessions = InteractionSession.objects(
        student=user,
        topic=topic,
    ).order_by("-started_at")

    session_history = []

    for session in sessions:
        messages = InteractionMessage.objects(
            session=session,
        ).order_by("created_at")

        latest_message = InteractionMessage.objects(
            session=session,
        ).order_by("-created_at").first()

        preview = "No message yet."

        if latest_message:
            preview = latest_message.content or "No message yet."

            if len(preview) > 80:
                preview = preview[:80] + "..."

        session_history.append({
            "session": session,
            "messages": messages,
            "message_count": messages.count(),
            "preview": preview,
        })

    return render_template(
        "interaction_topic_history.html",
        topic=topic,
        persona=persona,
        persona_name=persona["role_name"],
        persona_emoji=persona["emoji"],
        session_history=session_history,
    )


@interaction_bp.route("/student/interaction/topic/<topic_id>/start", methods=["POST", "GET"])
@login_required
def start_interaction_session(topic_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    topic = InteractionTopic.objects.get(id=topic_id)

    if not is_topic_unlocked(user, topic):
        flash("This interaction topic is locked. 此互動主題尚未解鎖。", "warning")
        return redirect(url_for("interaction.interaction_topics"))

    session = InteractionSession(
        student=user,
        topic=topic,
        completed=False,
        score=0,
        feedback="",
        xp_gained=0,
        started_at=datetime.utcnow(),
    )
    session.save()

    persona = gemini_service.get_topic_persona(topic)

    initial_message = (
        f"Scenario started: {topic.title}. "
        f"I will act as your {persona['role_name']}. "
        "Please answer in English. When you want to end, click Finish & Evaluate."
    )

    InteractionMessage(
        session=session,
        role="assistant",
        content=initial_message,
        created_at=datetime.utcnow(),
    ).save()

    return redirect(url_for("interaction.interaction_chat", session_id=session.id))


@interaction_bp.route("/student/interaction/session/<session_id>", methods=["GET", "POST"])
@login_required
def interaction_chat(session_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    session = InteractionSession.objects.get(id=session_id)

    if str(session.student.id) != str(user.id):
        return "Unauthorized", 403

    if session.completed:
        return redirect(url_for("interaction.interaction_result", session_id=session.id))

    topic = session.topic
    persona = gemini_service.get_topic_persona(topic)

    if request.method == "POST":
        action = request.form.get("action", "send")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if action == "finish":
            if is_ajax:
                return jsonify({
                    "ok": True,
                    "redirect_url": url_for("interaction.finish_interaction_session", session_id=session.id),
                })

            return redirect(url_for("interaction.finish_interaction_session", session_id=session.id))

        user_message = request.form.get("message", "").strip()

        if not user_message:
            if is_ajax:
                return jsonify({
                    "ok": False,
                    "error": "Please enter a message. 請輸入訊息。",
                }), 400

            flash("Please enter a message. 請輸入訊息。", "warning")
            return redirect(url_for("interaction.interaction_chat", session_id=session.id))

        user_created_at = datetime.utcnow()

        user_message_doc = InteractionMessage(
            session=session,
            role="user",
            content=user_message,
            created_at=user_created_at,
        )
        user_message_doc.save()

        message_xp = safe_add_xp(user, 2)
        session.xp_gained = getattr(session, "xp_gained", 0) + message_xp
        session.save()

        messages = InteractionMessage.objects(session=session).order_by("created_at")

        try:
            assistant_reply = gemini_service.generate_reply(
                topic=topic,
                student=user,
                messages=messages,
                user_message=user_message,
            )
        except Exception as e:
            print(f"[Interaction Chat] Failed to generate reply: {e}")
            assistant_reply = (
                "Sorry, I could not generate a reply right now. Please try again.\n"
                "抱歉，我現在無法產生回覆，請稍後再試。"
            )

        assistant_created_at = datetime.utcnow()

        assistant_message_doc = InteractionMessage(
            session=session,
            role="assistant",
            content=assistant_reply,
            created_at=assistant_created_at,
        )
        assistant_message_doc.save()

        if is_ajax:
            return jsonify({
                "ok": True,
                "user_message": {
                    "id": str(user_message_doc.id),
                    "role": "user",
                    "content": user_message_doc.content,
                    "created_at": user_created_at.isoformat(),
                },
                "assistant_message": {
                    "id": str(assistant_message_doc.id),
                    "role": "assistant",
                    "content": assistant_message_doc.content,
                    "created_at": assistant_created_at.isoformat(),
                },
                "xp_added": message_xp,
                "session_xp_gained": session.xp_gained,
            })

        return redirect(url_for("interaction.interaction_chat", session_id=session.id))

    messages = InteractionMessage.objects(session=session).order_by("created_at")

    topic_sessions = get_topic_sessions(user, topic)
    session_history = []

    for item in topic_sessions:
        history_messages = InteractionMessage.objects(
            session=item,
        ).order_by("created_at")

        session_history.append({
            "id": str(item.id),
            "started_at": item.started_at,
            "completed": item.completed,
            "score": item.score,
            "xp_gained": item.xp_gained,
            "message_count": history_messages.count(),
            "preview": get_session_preview(item),
            "is_current": str(item.id) == str(session.id),
            "messages": history_messages,
        })

    return render_template(
        "interaction_chat.html",
        session=session,
        topic=topic,
        messages=messages,
        session_history=session_history,
        persona=persona,
        persona_name=persona["role_name"],
        persona_emoji=persona["emoji"],
    )


def split_bilingual_text(text):
    text = str(text or "").strip()

    if not text:
        return "", ""

    separators = ["|||", " / ", "／", " | "]

    for separator in separators:
        if separator in text:
            english, chinese = text.split(separator, 1)
            return english.strip(), chinese.strip()

    for index, char in enumerate(text):
        if "\u4e00" <= char <= "\u9fff":
            english = text[:index].strip()
            chinese = text[index:].strip()

            if english and chinese:
                return english, chinese

    return text, ""


def build_feedback_items(feedback_text):
    label_map = {
        "Overall Feedback": ("Overall Feedback", "整體回饋"),
        "Fluency": ("Fluency", "流暢度"),
        "Vocabulary": ("Vocabulary", "單字用法"),
        "Grammar": ("Grammar", "文法"),
        "Next Suggestion": ("Next Suggestion", "下一步建議"),
        "Overall Feedback / 整體回饋": ("Overall Feedback", "整體回饋"),
        "Fluency / 流暢度": ("Fluency", "流暢度"),
        "Vocabulary / 單字用法": ("Vocabulary", "單字用法"),
        "Grammar / 文法": ("Grammar", "文法"),
        "Next Suggestion / 下一步建議": ("Next Suggestion", "下一步建議"),
    }

    items = []

    for raw_line in str(feedback_text or "").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if ":" in line:
            raw_label, content = line.split(":", 1)
            label_en, label_zh = label_map.get(raw_label.strip(), (raw_label.strip(), ""))
            content = content.strip()
        else:
            label_en, label_zh = "Feedback", "回饋"
            content = line

        content_en, content_zh = split_bilingual_text(content)

        if content_en or content_zh:
            items.append({
                "label_en": label_en,
                "label_zh": label_zh,
                "content_en": content_en,
                "content_zh": content_zh,
            })

    if not items:
        items.append({
            "label_en": "Feedback",
            "label_zh": "回饋",
            "content_en": "No feedback available yet.",
            "content_zh": "目前尚無回饋內容。",
        })

    return items


@interaction_bp.route("/student/interaction/session/<session_id>/finish", methods=["POST", "GET"])
@login_required
def finish_interaction_session(session_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    session = InteractionSession.objects.get(id=session_id)

    if str(session.student.id) != str(user.id):
        return "Unauthorized", 403

    if session.completed:
        return redirect(url_for("interaction.interaction_result", session_id=session.id))

    topic = session.topic
    messages = InteractionMessage.objects(session=session).order_by("created_at")

    evaluation = gemini_service.evaluate_session(
        topic=topic,
        student=user,
        messages=messages,
    )

    score = evaluation.get("score", 70)

    completion_xp = getattr(topic, "xp_reward", 10)

    if score >= 70:
        completion_xp += 5

    if score >= 85:
        completion_xp += 10

    if score >= 95:
        completion_xp += 15

    gained = safe_add_xp(user, completion_xp)

    feedback_text = (
        f"Overall Feedback: {evaluation.get('feedback', '')}\n"
        f"Fluency: {evaluation.get('fluency_feedback', '')}\n"
        f"Vocabulary: {evaluation.get('vocabulary_feedback', '')}\n"
        f"Grammar: {evaluation.get('grammar_feedback', '')}\n"
        f"Next Suggestion: {evaluation.get('next_suggestion', '')}"
    )

    session.score = score
    session.feedback = feedback_text
    session.completed = True
    session.completed_at = datetime.utcnow()
    session.xp_gained = getattr(session, "xp_gained", 0) + gained
    session.save()

    return redirect(url_for("interaction.interaction_result", session_id=session.id))


@interaction_bp.route("/student/interaction/session/<session_id>/result")
@login_required
def interaction_result(session_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    session = InteractionSession.objects.get(id=session_id)

    if str(session.student.id) != str(user.id):
        return "Unauthorized", 403

    topic = session.topic
    persona = gemini_service.get_topic_persona(topic)
    messages = InteractionMessage.objects(session=session).order_by("created_at")
    feedback_items = build_feedback_items(getattr(session, "feedback", ""))

    return render_template(
        "interaction_result.html",
        session=session,
        topic=topic,
        messages=messages,
        feedback_items=feedback_items,
        persona=persona,
        persona_name=persona["role_name"],
        persona_emoji=persona["emoji"],
    )