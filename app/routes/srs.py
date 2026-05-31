import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.services.srs_service import SRSManager, SuperMemo2Strategy
from app.repositories.word_repository import WordRepository
from app.services.level_system import LevelSystem
from app.services.achievement_service import AchievementService

from app.models.word import Word
from app.models.vocabulary_review_log import VocabularyReviewLog
from app.models.vocabulary_practice_log import VocabularyPracticeLog


srs_bp = Blueprint("srs", __name__)

word_repo = WordRepository()
srs_strategy = SuperMemo2Strategy()
srs_manager = SRSManager(strategy=srs_strategy, word_repository=word_repo)

level_system = LevelSystem()
achievement_service = AchievementService()


def get_xp_by_quality(quality: int) -> int:
    """
    Base XP rule for vocabulary review.

    Forgot = +2 XP
    Hard   = +5 XP
    Easy   = +8 XP
    """

    if quality <= 2:
        return 2

    if quality == 3:
        return 5

    return 8


def get_review_milestone_bonus(review_count: int) -> int:
    """
    Extra XP bonus based on total vocabulary review count.

    The higher the milestone, the harder it is to reach,
    but the bonus becomes larger.
    """

    milestone_bonus = {
        1: 2,
        5: 5,
        20: 15,
        50: 50
    }

    return milestone_bonus.get(review_count, 0)


def get_quality_label(quality: int) -> str:
    """
    Convert review quality score to readable label.
    """

    if quality <= 2:
        return "Forgot"

    if quality == 3:
        return "Hard"

    return "Easy"


def is_successful_review(quality: int) -> bool:
    """
    In self-reported vocabulary review:
    Forgot = unsuccessful
    Hard / Easy = successful
    """

    return quality >= 3


def get_latest_practice_log(user, word):
    """
    Get the latest sentence practice log for this user and word.
    If this returns None, it means this word was not practiced through
    sentence practice, so it should not appear in Vocabulary Review.
    """

    return VocabularyPracticeLog.objects(
        user=user,
        word=word
    ).order_by("-practiced_at").first()


@srs_bp.route("/review/list")
@login_required
def review_list():
    """
    Show vocabulary review queue.

    Important:
    Only words that have sentence practice records will be shown.
    This means course-only words or old automatically added words will be hidden.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    review_items = srs_manager.get_review_queue(current_user.id)

    now = datetime.datetime.utcnow()
    items = []

    for review_item in review_items:
        word = review_item.word

        latest_practice_log = get_latest_practice_log(user, word)

        # If the word has no sentence practice record,
        # do not show it in the review list.
        if not latest_practice_log:
            continue

        raw_seconds_left = (review_item.due_date - now).total_seconds()
        seconds_left = max(0, int(raw_seconds_left))
        is_due = raw_seconds_left <= 0

        if latest_practice_log.is_correct:
            practice_status = "Correct"
        else:
            practice_status = "Incorrect"

        items.append({
            "word": word,
            "review_item": review_item,
            "is_due": is_due,
            "seconds_left": seconds_left,

            "practice_status": practice_status,
            "practice_is_correct": latest_practice_log.is_correct,
            "practice_answer": latest_practice_log.user_answer,
            "practice_correct_answer": latest_practice_log.correct_answer,
            "practice_time": latest_practice_log.practiced_at
        })

    return render_template(
        "review_list.html",
        items=items
    )


@srs_bp.route("/review/next")
@login_required
def get_next_review_word():
    """
    Show the next due vocabulary review card.

    Only words that have sentence practice records can be reviewed.
    If exclude_word_id is provided, the system will skip that word.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    exclude_word_id = request.args.get("exclude_word_id")

    review_items = srs_manager.get_words_for_review(current_user.id, limit=10)

    selected_word = None

    for review_item in review_items:
        word = review_item.word

        if exclude_word_id and str(word.id) == str(exclude_word_id):
            continue

        latest_practice_log = get_latest_practice_log(user, word)

        # Skip words that were not added through sentence practice.
        if not latest_practice_log:
            continue

        selected_word = word
        break

    if not selected_word:
        return render_template(
            "review_card.html",
            word=None
        )

    return render_template(
        "review_card.html",
        word=selected_word
    )


@srs_bp.route("/review/word/<word_id>")
@login_required
def review_word(word_id):
    """
    Review a specific word from the review list.

    Only words that have sentence practice records can be reviewed.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()

    review_item = word_repo.get_review_item(current_user.id, word_id)

    if not review_item:
        flash("This word is not in your review queue.", "error")
        return redirect(url_for("srs.review_list"))

    latest_practice_log = get_latest_practice_log(user, review_item.word)

    if not latest_practice_log:
        flash("This word was not added through sentence practice.", "error")
        return redirect(url_for("srs.review_list"))

    now = datetime.datetime.utcnow()

    if review_item.due_date > now:
        flash("This word is not ready for review yet.", "error")
        return redirect(url_for("srs.review_list"))

    return render_template(
        "review_card.html",
        word=review_item.word
    )


@srs_bp.route("/review/submit", methods=["POST"])
@login_required
def submit_review():
    """
    Submit review result.

    quality:
    1 = Forgot
    3 = Hard
    5 = Easy
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    word_id = request.form.get("word_id")
    quality_str = request.form.get("quality")

    if not word_id or not quality_str:
        flash("Invalid review submission.", "error")
        return redirect(url_for("srs.review_list"))

    try:
        quality = int(quality_str)
    except ValueError:
        flash("Invalid quality value.", "error")
        return redirect(url_for("srs.review_list"))

    user = current_user._get_current_object()
    word = Word.objects(id=word_id).first()

    if not word:
        flash("Word not found.", "error")
        return redirect(url_for("srs.review_list"))

    latest_practice_log = get_latest_practice_log(user, word)

    # Prevent reviewing words that were not practiced through sentence practice.
    if not latest_practice_log:
        flash("This word was not added through sentence practice.", "error")
        return redirect(url_for("srs.review_list"))

    # 1. Update SRS next review time
    updated_review_item = srs_manager.process_review_result(
        current_user.id,
        word_id,
        quality
    )

    # 2. Base XP from review quality
    base_xp = get_xp_by_quality(quality)

    # 3. Increase total vocabulary review count
    current_user.vocabulary_review_count = getattr(
        current_user,
        "vocabulary_review_count",
        0
    ) + 1

    # 4. Extra milestone bonus XP
    milestone_bonus = get_review_milestone_bonus(
        current_user.vocabulary_review_count
    )

    # 5. Total XP gained this time
    xp_gained = base_xp + milestone_bonus

    # 6. Add XP
    current_user.add_xp(xp_gained)
    level_system.update_user_level(current_user)

    # 7. Check achievements after XP and level update
    achievement_service.check_level_badge(current_user)

    # 8. Save review history log
    VocabularyReviewLog(
        user=user,
        word=word,
        quality=quality,
        quality_label=get_quality_label(quality),
        is_successful=is_successful_review(quality),
        xp_gained=xp_gained,
        base_xp=base_xp,
        bonus_xp=milestone_bonus,
        next_review_at=updated_review_item.due_date
    ).save()

    # 9. Flash message
    if milestone_bonus > 0:
        flash(
            f"Review submitted! You gained {base_xp} XP + {milestone_bonus} bonus XP "
            f"for reaching {current_user.vocabulary_review_count} reviews!",
            "success"
        )
    else:
        flash(
            f"Review submitted! You gained {xp_gained} XP.",
            "success"
        )

    # 10. Go to next available review word
    return redirect(url_for("srs.get_next_review_word"))


@srs_bp.route("/review/stats")
@login_required
def review_stats():
    """
    Show vocabulary review statistics and recent review history.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()

    logs = VocabularyReviewLog.objects(user=user).order_by("-reviewed_at")

    total_reviews = logs.count()
    successful_reviews = logs.filter(is_successful=True).count()
    forgot_reviews = logs.filter(quality_label="Forgot").count()

    accuracy = 0

    if total_reviews > 0:
        accuracy = round((successful_reviews / total_reviews) * 100, 1)

    recent_logs = logs.limit(20)

    return render_template(
        "review_stats.html",
        total_reviews=total_reviews,
        successful_reviews=successful_reviews,
        forgot_reviews=forgot_reviews,
        accuracy=accuracy,
        recent_logs=recent_logs
    )