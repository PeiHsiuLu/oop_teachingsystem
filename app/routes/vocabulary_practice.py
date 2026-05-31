from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models.word import Word
from app.models.vocabulary_practice_log import VocabularyPracticeLog

from app.services.vocabulary_practice_service import VocabularyPracticeService
from app.services.cefr_level_service import CEFRLevelService
from app.services.level_system import LevelSystem
from app.services.achievement_service import AchievementService
from app.services.srs_service import SRSManager, SuperMemo2Strategy

from app.repositories.word_repository import WordRepository


vocabulary_practice_bp = Blueprint("vocabulary_practice", __name__)

practice_service = VocabularyPracticeService()
cefr_level_service = CEFRLevelService()
level_system = LevelSystem()
achievement_service = AchievementService()

word_repo = WordRepository()
srs_strategy = SuperMemo2Strategy()
srs_manager = SRSManager(strategy=srs_strategy, word_repository=word_repo)


@vocabulary_practice_bp.route("/practice", methods=["GET"])
@login_required
def practice_page():
    """
    Show one vocabulary fill-in-the-blank question.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    question = practice_service.generate_question_for_user(current_user)

    show_guide = not getattr(
        current_user,
        "has_seen_vocabulary_practice_guide",
        False
    )

    return render_template(
        "vocabulary_practice.html",
        question=question,
        result=None,
        show_guide=show_guide
    )


@vocabulary_practice_bp.route("/practice/submit", methods=["POST"])
@login_required
def submit_practice_answer():
    """
    Receive user's answer, check whether it is correct,
    record sentence practice history, update CEFR statistics,
    add XP, and add the word to the review queue.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    word_id = request.form.get("word_id")
    user_answer = request.form.get("user_answer")
    target_answer = request.form.get("target_answer")

    word = Word.objects(id=word_id).first()

    if not word:
        flash("Word not found.", "danger")
        return redirect(url_for("vocabulary_practice.practice_page"))

    # target_answer is the actual word form in the sentence.
    # Example:
    # word.word_text = "shoe"
    # target_answer = "shoes"
    correct_answer = target_answer if target_answer else word.word_text

    is_correct = practice_service.check_answer(correct_answer, user_answer)

    # 1. Record sentence practice history
    VocabularyPracticeLog(
        user=current_user._get_current_object(),
        word=word,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=is_correct,
        cefr_level_at_time=getattr(current_user, "cefr_level", "A1")
    ).save()

    # 2. Since the user has practiced this word,
    # add it to the vocabulary review queue.
    # The SRS service will prevent duplicate words from being added.
    srs_manager.add_word_to_review_queue(current_user.id, word.id)

    # 3. Add XP for sentence practice
    xp_gained = 10 if is_correct else 3

    current_user.add_xp(xp_gained)
    level_system.update_user_level(current_user)

    # 4. Check achievements after XP and level update
    achievement_service.check_level_badge(current_user)

    # 5. Update CEFR statistics and check CEFR level-up
    leveled_up = cefr_level_service.record_practice_result(
        current_user,
        is_correct
    )

    result = {
        "is_correct": is_correct,
        "user_answer": user_answer,
        "correct_answer": correct_answer,
        "word_text": word.word_text,
        "definition": word.definition,
        "part_of_speech": word.part_of_speech,
        "difficulty_level": word.difficulty_level,
        "example_sentence": word.example_sentences[0] if word.example_sentences else "",
        "current_cefr_level": current_user.cefr_level,
        "leveled_up": leveled_up,

        "xp_gained": xp_gained,
        "user_xp": current_user.xp,
        "user_level": current_user.level
    }

    return render_template(
        "vocabulary_practice.html",
        question=None,
        result=result,
        show_guide=False
    )


@vocabulary_practice_bp.route("/practice/guide/seen", methods=["POST"])
@login_required
def mark_practice_guide_seen():
    """
    Mark that the current student has already seen the vocabulary practice guide.
    This is stored in the user's account, not in the browser.
    """

    if current_user.role != "student":
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    current_user.has_seen_vocabulary_practice_guide = True
    current_user.save()

    return jsonify({
        "success": True,
        "message": "Vocabulary practice guide marked as seen."
    })