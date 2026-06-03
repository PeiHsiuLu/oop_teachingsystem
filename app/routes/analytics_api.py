import os
import json
import re
from datetime import datetime

from dotenv import load_dotenv
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from app.models.interaction import InteractionSession, InteractionMessage
from app.models.vocabulary_practice_log import VocabularyPracticeLog
from app.models.vocabulary_review_log import VocabularyReviewLog
from app.models.course import ChapterQuizAttempt
from app.models.word import ReviewItem


load_dotenv()

try:
    import google.generativeai as genai
except Exception as e:
    print(f"[Analytics Gemini] google.generativeai import failed: {e}")
    genai = None


analytics_bp = Blueprint("analytics", __name__)


def safe_average(values):
    cleaned = []

    for value in values:
        try:
            cleaned.append(float(value))
        except Exception:
            pass

    if not cleaned:
        return 0

    return round(sum(cleaned) / len(cleaned), 1)


def safe_percentage(numerator, denominator):
    try:
        denominator = int(denominator)
        numerator = int(numerator)
    except Exception:
        return 0

    if denominator <= 0:
        return 0

    return round((numerator / denominator) * 100, 1)


def safe_count(queryset):
    try:
        return queryset.count()
    except Exception:
        return 0


def get_word_text(word):
    if not word:
        return ""

    return getattr(word, "word_text", "") or ""


def get_quiz_weak_words(attempts, limit=8):
    weak_words = {}

    for attempt in attempts:
        answers = getattr(attempt, "answers", []) or []

        for answer in answers:
            is_correct = getattr(answer, "is_correct", True)

            if is_correct:
                continue

            target_word = (
                getattr(answer, "target_word", "")
                or getattr(answer, "correct_answer", "")
                or "Unknown"
            )

            target_word = str(target_word).strip()

            if not target_word:
                continue

            weak_words[target_word] = weak_words.get(target_word, 0) + 1

    sorted_words = sorted(
        weak_words.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        {
            "word": word,
            "wrong_count": count
        }
        for word, count in sorted_words[:limit]
    ]


def get_practice_weak_words(practice_logs, limit=8):
    weak_words = {}

    for log in practice_logs:
        is_correct = getattr(log, "is_correct", False)

        if is_correct:
            continue

        word_text = get_word_text(getattr(log, "word", None))

        if not word_text:
            continue

        weak_words[word_text] = weak_words.get(word_text, 0) + 1

    sorted_words = sorted(
        weak_words.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        {
            "word": word,
            "wrong_count": count
        }
        for word, count in sorted_words[:limit]
    ]


def get_review_weak_words(review_logs, limit=8):
    weak_words = {}

    for log in review_logs:
        quality_label = str(getattr(log, "quality_label", "") or "")

        if quality_label not in ["Forgot", "Hard"]:
            continue

        word_text = get_word_text(getattr(log, "word", None))

        if not word_text:
            continue

        weak_words[word_text] = weak_words.get(word_text, 0) + 1

    sorted_words = sorted(
        weak_words.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        {
            "word": word,
            "count": count
        }
        for word, count in sorted_words[:limit]
    ]


def collect_student_learning_data(student):
    """
    Collect all learning data needed for Gemini analysis.
    This function is defensive: if one section fails, the page still works.
    """

    data = {
        "student": {
            "username": getattr(student, "username", "Student"),
            "xp": getattr(student, "xp", 0) or 0,
            "level": getattr(student, "level", 1) or 1,
            "cefr_level": getattr(student, "cefr_level", "A1") or "A1",
            "credit_score": getattr(student, "credit_score", 100) or 100,
        },
        "conversation": {
            "completed_sessions": 0,
            "total_sessions": 0,
            "average_score": 0,
            "best_score": 0,
            "latest_score": None,
            "total_user_messages": 0,
            "average_user_messages_per_completed_session": 0,
        },
        "vocabulary_practice": {
            "total_attempts": 0,
            "correct_attempts": 0,
            "accuracy": 0,
            "weak_words": [],
            "recent_attempts": [],
        },
        "vocabulary_review": {
            "total_reviews": 0,
            "successful_reviews": 0,
            "success_rate": 0,
            "forgot_reviews": 0,
            "hard_reviews": 0,
            "easy_reviews": 0,
            "weak_words": [],
            "review_queue_total": 0,
            "review_ready_now": 0,
        },
        "quiz": {
            "total_attempts": 0,
            "average_score": 0,
            "best_score": 0,
            "latest_score": None,
            "weak_words": [],
            "recent_attempts": [],
        },
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }

    # ============================================================
    # Conversation / AI Chat
    # ============================================================

    try:
        all_sessions = InteractionSession.objects(student=student)
        completed_sessions = InteractionSession.objects(
            student=student,
            completed=True
        ).order_by("-completed_at", "-started_at")

        completed_scores = [
            getattr(session, "score", 0) or 0
            for session in completed_sessions
        ]

        total_user_messages = 0

        for session in completed_sessions:
            total_user_messages += InteractionMessage.objects(
                session=session,
                role="user"
            ).count()

        completed_count = completed_sessions.count()

        data["conversation"] = {
            "completed_sessions": completed_count,
            "total_sessions": all_sessions.count(),
            "average_score": safe_average(completed_scores),
            "best_score": max(completed_scores) if completed_scores else 0,
            "latest_score": completed_scores[0] if completed_scores else None,
            "total_user_messages": total_user_messages,
            "average_user_messages_per_completed_session": (
                round(total_user_messages / completed_count, 1)
                if completed_count > 0 else 0
            ),
        }

    except Exception as e:
        print(f"[Analytics] Conversation data failed: {e}")

    # ============================================================
    # Vocabulary Practice
    # ============================================================

    try:
        practice_logs = VocabularyPracticeLog.objects(user=student).order_by("-practiced_at")
        correct_count = VocabularyPracticeLog.objects(user=student, is_correct=True).count()
        total_count = practice_logs.count()

        recent_attempts = []

        for log in practice_logs[:8]:
            recent_attempts.append({
                "word": get_word_text(getattr(log, "word", None)),
                "user_answer": getattr(log, "user_answer", "") or "",
                "correct_answer": getattr(log, "correct_answer", "") or "",
                "is_correct": bool(getattr(log, "is_correct", False)),
                "cefr_level": getattr(log, "cefr_level_at_time", "A1") or "A1",
            })

        data["vocabulary_practice"] = {
            "total_attempts": total_count,
            "correct_attempts": correct_count,
            "accuracy": safe_percentage(correct_count, total_count),
            "weak_words": get_practice_weak_words(practice_logs, limit=8),
            "recent_attempts": recent_attempts,
        }

    except Exception as e:
        print(f"[Analytics] Vocabulary practice data failed: {e}")

    # ============================================================
    # Vocabulary Review / SRS
    # ============================================================

    try:
        review_logs = VocabularyReviewLog.objects(user=student).order_by("-reviewed_at")
        successful_reviews = VocabularyReviewLog.objects(
            user=student,
            is_successful=True
        ).count()

        forgot_reviews = VocabularyReviewLog.objects(
            user=student,
            quality_label="Forgot"
        ).count()

        hard_reviews = VocabularyReviewLog.objects(
            user=student,
            quality_label="Hard"
        ).count()

        easy_reviews = VocabularyReviewLog.objects(
            user=student,
            quality_label="Easy"
        ).count()

        review_queue = ReviewItem.objects(user=student)
        now = datetime.utcnow()
        ready_now = 0

        for item in review_queue:
            due_date = getattr(item, "due_date", None)

            if due_date and due_date <= now:
                ready_now += 1

        total_reviews = review_logs.count()

        data["vocabulary_review"] = {
            "total_reviews": total_reviews,
            "successful_reviews": successful_reviews,
            "success_rate": safe_percentage(successful_reviews, total_reviews),
            "forgot_reviews": forgot_reviews,
            "hard_reviews": hard_reviews,
            "easy_reviews": easy_reviews,
            "weak_words": get_review_weak_words(review_logs, limit=8),
            "review_queue_total": review_queue.count(),
            "review_ready_now": ready_now,
        }

    except Exception as e:
        print(f"[Analytics] Vocabulary review data failed: {e}")

    # ============================================================
    # Chapter Quiz
    # ============================================================

    try:
        quiz_attempts = ChapterQuizAttempt.objects(student=student).order_by("-created_at")
        quiz_scores = [
            getattr(attempt, "score", 0) or 0
            for attempt in quiz_attempts
        ]

        recent_attempts = []

        for attempt in quiz_attempts[:8]:
            chapter = getattr(attempt, "chapter", None)

            recent_attempts.append({
                "chapter_title": getattr(chapter, "title", "Chapter") if chapter else "Chapter",
                "score": getattr(attempt, "score", 0) or 0,
                "correct_count": getattr(attempt, "correct_count", 0) or 0,
                "total_questions": getattr(attempt, "total_questions", 5) or 5,
            })

        data["quiz"] = {
            "total_attempts": quiz_attempts.count(),
            "average_score": safe_average(quiz_scores),
            "best_score": max(quiz_scores) if quiz_scores else 0,
            "latest_score": quiz_scores[0] if quiz_scores else None,
            "weak_words": get_quiz_weak_words(quiz_attempts, limit=8),
            "recent_attempts": recent_attempts,
        }

    except Exception as e:
        print(f"[Analytics] Quiz data failed: {e}")

    return data


def build_fallback_analysis(learning_data):
    student = learning_data["student"]
    conversation = learning_data["conversation"]
    practice = learning_data["vocabulary_practice"]
    review = learning_data["vocabulary_review"]
    quiz = learning_data["quiz"]

    composite_score = 50

    if practice["total_attempts"] > 0:
        composite_score += min(15, practice["accuracy"] * 0.15)

    if quiz["total_attempts"] > 0:
        composite_score += min(15, quiz["average_score"] * 0.15)

    if conversation["completed_sessions"] > 0:
        composite_score += min(15, conversation["average_score"] * 0.15)

    if review["total_reviews"] > 0:
        composite_score += min(5, review["success_rate"] * 0.05)

    composite_score = int(max(0, min(100, round(composite_score))))

    weak_words = []

    for item in practice.get("weak_words", []):
        weak_words.append(item["word"])

    for item in review.get("weak_words", []):
        weak_words.append(item["word"])

    for item in quiz.get("weak_words", []):
        weak_words.append(item["word"])

    weak_words = list(dict.fromkeys([word for word in weak_words if word]))[:8]

    if not weak_words:
        weak_words = ["No obvious weak words yet"]

    return {
        "source": "fallback",
        "overall_status_en": "Learning data collected successfully. Keep practicing consistently.",
        "overall_status_zh": "已成功整理你的學習資料。建議保持穩定練習。",
        "cefr_assessment_en": f"Your current CEFR level is {student['cefr_level']}. This should be treated as a system estimate and can improve with more practice data.",
        "cefr_assessment_zh": f"你目前的 CEFR 等級是 {student['cefr_level']}。這是系統估計值，之後可以透過更多練習資料逐步調整。",
        "conversation_ability_en": (
            f"You completed {conversation['completed_sessions']} AI chat sessions with an average score of "
            f"{conversation['average_score']}."
        ),
        "conversation_ability_zh": (
            f"你已完成 {conversation['completed_sessions']} 次 AI 情境對話，平均分數為 "
            f"{conversation['average_score']}。"
        ),
        "sentence_ability_en": (
            f"Your sentence practice accuracy is {practice['accuracy']}% "
            f"across {practice['total_attempts']} attempts."
        ),
        "sentence_ability_zh": (
            f"你的句子填空練習正確率為 {practice['accuracy']}%，"
            f"共完成 {practice['total_attempts']} 次練習。"
        ),
        "quiz_ability_en": (
            f"Your chapter quiz average score is {quiz['average_score']}."
        ),
        "quiz_ability_zh": (
            f"你的章節 Quiz 平均分數為 {quiz['average_score']}。"
        ),
        "vocabulary_ability_en": (
            f"Your vocabulary review success rate is {review['success_rate']}%."
        ),
        "vocabulary_ability_zh": (
            f"你的單字複習成功率為 {review['success_rate']}%。"
        ),
        "composite_score": composite_score,
        "strengths": [
            {
                "en": "You are building learning records across multiple activities.",
                "zh": "你正在透過多種活動累積學習紀錄。"
            },
            {
                "en": "The system can now track vocabulary, quiz, review, and AI chat progress together.",
                "zh": "系統現在可以綜合追蹤單字、Quiz、複習與 AI 對話進度。"
            }
        ],
        "weaknesses": [
            {
                "en": "Your weaker words should be reviewed more often.",
                "zh": "較不熟的單字需要更頻繁複習。"
            },
            {
                "en": "Try to answer AI chat questions with longer complete sentences.",
                "zh": "AI 對話時可以嘗試用更完整、更長的句子回答。"
            }
        ],
        "recommended_actions": [
            {
                "en": "Review ready SRS words first.",
                "zh": "優先複習目前已到期的 SRS 單字。"
            },
            {
                "en": "Redo chapter quizzes with low scores.",
                "zh": "重新練習分數較低的章節 Quiz。"
            },
            {
                "en": "Complete one AI chat session and focus on giving 2 to 3 sentence replies.",
                "zh": "完成一次 AI 情境對話，並練習每次回答 2 到 3 句。"
            }
        ],
        "review_strategy_en": "Focus on weak words first, then use them in sentence practice and AI chat.",
        "review_strategy_zh": "先複習弱點單字，再把它們用在句子練習與 AI 情境對話中。",
        "weak_words": weak_words
    }


def build_gemini_prompt(learning_data):
    data_json = json.dumps(
        learning_data,
        ensure_ascii=False,
        indent=2,
        default=str
    )

    return f"""
You are an English learning analytics assistant.

Analyze this student's learning data from an English learning platform.

The platform includes:
1. CEFR level
2. AI role-play conversation practice
3. Sentence fill-in-the-blank vocabulary practice
4. Chapter vocabulary quizzes
5. SRS vocabulary review
6. Overall learning progress

Important output rules:
- Return ONLY valid JSON.
- Do not use markdown code fences.
- Use English and Traditional Chinese.
- Be encouraging but honest.
- Keep each field concise.
- Do not invent data that is not supported by the provided JSON.
- If data is insufficient, clearly say that more data is needed.
- composite_score must be an integer from 0 to 100.

Student learning data:
{data_json}

Return this JSON format exactly:
{{
  "source": "gemini",
  "overall_status_en": "short English overview",
  "overall_status_zh": "繁體中文整體狀態",
  "cefr_assessment_en": "English CEFR assessment",
  "cefr_assessment_zh": "繁體中文 CEFR 分析",
  "conversation_ability_en": "English AI chat ability analysis",
  "conversation_ability_zh": "繁體中文 AI 對話能力分析",
  "sentence_ability_en": "English sentence construction analysis",
  "sentence_ability_zh": "繁體中文句子建構能力分析",
  "quiz_ability_en": "English quiz performance analysis",
  "quiz_ability_zh": "繁體中文 Quiz 表現分析",
  "vocabulary_ability_en": "English vocabulary and review analysis",
  "vocabulary_ability_zh": "繁體中文單字與複習分析",
  "composite_score": 75,
  "strengths": [
    {{"en": "strength 1", "zh": "優點 1"}},
    {{"en": "strength 2", "zh": "優點 2"}}
  ],
  "weaknesses": [
    {{"en": "weakness 1", "zh": "弱點 1"}},
    {{"en": "weakness 2", "zh": "弱點 2"}}
  ],
  "recommended_actions": [
    {{"en": "action 1", "zh": "建議 1"}},
    {{"en": "action 2", "zh": "建議 2"}},
    {{"en": "action 3", "zh": "建議 3"}}
  ],
  "review_strategy_en": "English review strategy",
  "review_strategy_zh": "繁體中文複習策略",
  "weak_words": ["word1", "word2", "word3"]
}}
"""


def parse_json_from_text(text):
    if not text:
        return {}

    cleaned = str(text).strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}

    return {}


def generate_gemini_analysis(learning_data):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip().strip('"').strip("'")

    if not genai:
        fallback = build_fallback_analysis(learning_data)
        fallback["gemini_error"] = "google.generativeai is not available."
        return fallback

    if not api_key:
        fallback = build_fallback_analysis(learning_data)
        fallback["gemini_error"] = "GEMINI_API_KEY is empty."
        return fallback

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        prompt = build_gemini_prompt(learning_data)
        response = model.generate_content(prompt)
        text = getattr(response, "text", "")

        data = parse_json_from_text(text)

        if not data:
            fallback = build_fallback_analysis(learning_data)
            fallback["gemini_error"] = "Gemini returned non-JSON content."
            return fallback

        fallback = build_fallback_analysis(learning_data)

        # Fill missing fields with fallback values to avoid frontend errors.
        for key, value in fallback.items():
            if key not in data or data[key] in [None, ""]:
                data[key] = value

        data["source"] = "gemini"
        return data

    except Exception as e:
        print(f"[Analytics Gemini] Failed: {e}")

        fallback = build_fallback_analysis(learning_data)
        fallback["gemini_error"] = str(e)
        return fallback


@analytics_bp.route("/student/analytics", methods=["GET"])
@login_required
def student_analytics_page():
    if current_user.role != "student":
        return "Unauthorized", 403

    return render_template("student_analytics.html")


@analytics_bp.route("/api/analytics/report", methods=["GET"])
@login_required
def get_analytics_report():
    if current_user.role != "student":
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 403

    student = current_user._get_current_object()

    learning_data = collect_student_learning_data(student)
    analysis = generate_gemini_analysis(learning_data)

    return jsonify({
        "ok": True,
        "learning_data": learning_data,
        "analysis": analysis,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }), 200