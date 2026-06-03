import re
from datetime import datetime

import markdown
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.course import (
    LearningPath,
    Chapter,
    Unit,
    QuizQuestion,
    UnlockRule,
    QuizAnswerRecord,
    ChapterQuizAttempt,
)

from app.models.forms import CreatePathForm, AddChapterForm, AddUnitForm
from app.models.report import Report
from app.models.word import Word, ReviewItem
from app.models.vocabulary_practice_log import VocabularyPracticeLog
from app.models.analytics import Progress

from app.services.course_service import CourseService
from app.services.leaderboard_service import LeaderboardService
from app.services.vocabulary_service import VocabularyService
from app.services.level_system import LevelSystem
from app.services.achievement_service import AchievementService
from app.services.course_vocabulary_service import CourseVocabularyService

try:
    from app.utils.decorators import no_cache
except Exception:
    def no_cache(func):
        return func


course_bp = Blueprint("course", __name__)

course_service = CourseService()
leaderboard_service = LeaderboardService()
vocab_service = VocabularyService()
level_system = LevelSystem()
achievement_service = AchievementService()
course_vocabulary_service = CourseVocabularyService()


# ============================================================
# Helper functions
# ============================================================

def safe_add_xp(user, xp_amount):
    """
    Add XP safely and update level / achievement if available.
    """

    if not user or xp_amount <= 0:
        return 0

    try:
        if hasattr(user, "add_xp"):
            user.add_xp(xp_amount)
        else:
            current_xp = getattr(user, "xp", 0)
            user.xp = current_xp + xp_amount
            user.save()

        try:
            level_system.update_user_level(user)
        except Exception as e:
            print(f"[XP] Level update skipped: {e}")

        try:
            achievement_service.check_level_badge(user)
        except Exception as e:
            print(f"[XP] Achievement check skipped: {e}")

        return xp_amount

    except Exception as e:
        print(f"[XP] Failed to add XP: {e}")
        return 0


def get_path_display_name(path):
    """
    Support path_name / name / title.
    """

    if not path:
        return ""

    path_name = getattr(path, "path_name", "")

    if path_name:
        return path_name

    name = getattr(path, "name", "")

    if name:
        return name

    title = getattr(path, "title", "")

    if title:
        return title

    return ""


def get_path_index_by_unit(unit):
    """
    Find which LearningPath this unit belongs to.
    Used by CourseVocabularyService to decide target CEFR level.
    """

    if not unit:
        return 1

    for path in LearningPath.objects.all():
        for chapter in getattr(path, "chapters", []):
            for path_unit in getattr(chapter, "units", []):
                if str(path_unit.id) == str(unit.id):
                    path_name = get_path_display_name(path)

                    if "Path 1" in path_name or "菜鳥出國" in path_name:
                        return 1

                    if "Path 2" in path_name or "日常生活" in path_name:
                        return 2

                    if "Path 3" in path_name or "職場" in path_name:
                        return 3

                    if "Path 4" in path_name or "時事" in path_name:
                        return 4

                    if "Path 5" in path_name or "英文學術" in path_name:
                        return 5

                    return 1

    return 1


def get_chapter_by_unit(unit):
    """
    Find the chapter that owns this unit.
    """

    if not unit:
        return None

    for chapter in Chapter.objects.all():
        for chapter_unit in getattr(chapter, "units", []):
            if str(chapter_unit.id) == str(unit.id):
                return chapter

    return None


def get_all_ordered_chapters():
    """
    Return all chapters in global learning order.

    Important:
    This keeps the order:
    Path 1 Chapter 1
    Path 1 Chapter 2
    Path 2 Chapter 1
    Path 2 Chapter 2
    Path 3 Chapter 1
    ...

    This is required because the first chapter of Path 2 should check
    the last chapter of Path 1 as its previous chapter.
    """

    ordered_chapters = []

    for path in LearningPath.objects.all():
        for chapter in getattr(path, "chapters", []):
            ordered_chapters.append(chapter)

    return ordered_chapters


def get_previous_chapter(target_chapter):
    """
    Find the previous chapter across all learning paths.

    Logic:
    - Path 1 Chapter 1 has no previous chapter.
    - Path 1 Chapter 2 uses Path 1 Chapter 1.
    - Path 2 Chapter 1 uses Path 1's last chapter.
    - Path 3 Chapter 1 uses Path 2's last chapter.
    """

    if not target_chapter:
        return None

    ordered_chapters = get_all_ordered_chapters()

    for index, chapter in enumerate(ordered_chapters):
        if str(chapter.id) == str(target_chapter.id):
            if index == 0:
                return None

            return ordered_chapters[index - 1]

    return None


def get_best_quiz_score(user, chapter):
    """
    Get user's best quiz score for a specific chapter.
    """

    if not user or not chapter:
        return 0

    best_attempt = ChapterQuizAttempt.objects(
        student=user,
        chapter=chapter
    ).order_by("-score").first()

    if best_attempt:
        return best_attempt.score

    return 0


def cefr_to_rank(cefr_level):
    """
    Convert CEFR level to comparable rank.
    """

    levels = {
        "A1": 1,
        "A2": 2,
        "B1": 3,
        "B2": 4,
        "C1": 5,
        "C2": 6,
    }

    return levels.get(str(cefr_level).upper(), 1)


def check_chapter_unlocked(user, chapter):
    """
    Correct chapter unlock logic.

    Important:
    - level rule checks current user level
    - cefr rule checks current user CEFR
    - score rule checks PREVIOUS chapter best score across all paths

    Example:
    Path 2 Chapter 1 with Quiz Score >= 80 checks Path 1 Chapter 2 best score.
    """

    if not user or not chapter:
        return False

    unlock_rules = getattr(chapter, "unlock_rules", [])

    if not unlock_rules:
        try:
            return chapter.is_unlocked(user)
        except Exception:
            return True

    previous_chapter = get_previous_chapter(chapter)

    for rule in unlock_rules:
        rule_type = getattr(rule, "rule_type", "none")
        value = getattr(rule, "value", "")

        if rule_type == "none":
            continue

        if rule_type == "level":
            try:
                required_level = int(value)
            except ValueError:
                required_level = 0

            user_level = getattr(user, "level", 1)

            if user_level < required_level:
                return False

        elif rule_type == "score":
            try:
                required_score = int(value)
            except ValueError:
                required_score = 0

            # Only the very first chapter in the entire course can skip score rule.
            if previous_chapter is None:
                continue

            previous_best_score = get_best_quiz_score(user, previous_chapter)

            if previous_best_score < required_score:
                return False

        elif rule_type == "cefr":
            user_cefr = getattr(user, "cefr_level", "A1")

            if cefr_to_rank(user_cefr) < cefr_to_rank(value):
                return False

    return True


def has_completed_unit(user, unit):
    """
    Check whether the student has completed/read this unit.
    Uses existing Progress model.
    """

    if not user or not unit:
        return False

    return Progress.objects(
        student=user,
        unit=unit
    ).first() is not None


def mark_unit_completed(user, unit):
    """
    Mark unit as completed.

    Current demo rule:
    entering a unit page means this unit is completed.
    """

    if not user or not unit:
        return False

    existing = Progress.objects(
        student=user,
        unit=unit
    ).first()

    if existing:
        return True

    try:
        Progress(
            student=user,
            unit=unit
        ).save()

        print(f"[Progress] Unit completed: {unit.title}")
        return True

    except Exception as e:
        print(f"[Progress] Failed to mark unit completed: {e}")
        return False


def can_access_unit(user, chapter, unit):
    """
    Unit access rule:
    - Unit 1 can be accessed directly.
    - Unit 2 requires Unit 1 completed.
    - Unit 3 requires Unit 2 completed, and so on.
    """

    if not user or not chapter or not unit:
        return False

    if not check_chapter_unlocked(user, chapter):
        return False

    units = list(getattr(chapter, "units", []))

    if not units:
        return False

    target_index = None

    for index, chapter_unit in enumerate(units):
        if str(chapter_unit.id) == str(unit.id):
            target_index = index
            break

    if target_index is None:
        return False

    if target_index == 0:
        return True

    previous_unit = units[target_index - 1]

    return has_completed_unit(user, previous_unit)


def can_take_chapter_quiz(user, chapter):
    """
    Quiz access rule:
    Student can take quiz only when:
    1. Chapter is unlocked.
    2. Quiz is ready.
    3. All units in this chapter are completed.
    """

    if not user or not chapter:
        return False

    if not check_chapter_unlocked(user, chapter):
        return False

    if not chapter.is_quiz_ready():
        return False

    units = list(getattr(chapter, "units", []))

    if not units:
        return False

    for unit in units:
        if not has_completed_unit(user, unit):
            return False

    return True


def get_word_text_safely(word):
    """
    Get English word text from Word document safely.
    """

    if not word:
        return ""

    for field_name in ["word_text", "word", "english", "term", "vocabulary"]:
        value = getattr(word, field_name, None)

        if value:
            return str(value).strip()

    return ""


def get_word_by_text(target_word):
    """
    Find Word by possible field names.
    Your current Word model mainly uses Word.word_text.
    """

    if not target_word:
        return None

    target_word = target_word.strip()

    if not target_word:
        return None

    possible_fields = [
        "word_text",
        "word",
        "english",
        "term",
        "vocabulary",
    ]

    for field_name in possible_fields:
        try:
            if field_name in Word._fields:
                word = Word.objects(
                    __raw__={
                        field_name: {
                            "$regex": f"^{re.escape(target_word)}$",
                            "$options": "i"
                        }
                    }
                ).first()

                if word:
                    return word

        except Exception as e:
            print(f"[Quiz Review] Search field {field_name} failed: {e}")

    print(f"[Quiz Review] Word not found: {target_word}")
    return None


def create_or_get_review_item(user, word):
    """
    Create ReviewItem directly.

    This is important because review_list reads from ReviewItem.
    """

    if not user or not word:
        return None

    existing = ReviewItem.objects(
        user=user,
        word=word
    ).first()

    if existing:
        print(f"[Quiz Review] ReviewItem already exists: {get_word_text_safely(word)}")
        return existing

    try:
        fields = getattr(ReviewItem, "_fields", {})
        kwargs = {}

        if "user" in fields:
            kwargs["user"] = user

        if "word" in fields:
            kwargs["word"] = word

        if "due_date" in fields:
            kwargs["due_date"] = datetime.utcnow()

        if "interval" in fields:
            kwargs["interval"] = 0

        if "ease_factor" in fields:
            kwargs["ease_factor"] = 2.5

        if "review_count" in fields:
            kwargs["review_count"] = 0

        if "last_reviewed" in fields:
            kwargs["last_reviewed"] = datetime.utcnow()

        if "created_at" in fields:
            kwargs["created_at"] = datetime.utcnow()

        if "updated_at" in fields:
            kwargs["updated_at"] = datetime.utcnow()

        review_item = ReviewItem(**kwargs)
        review_item.save()

        print(f"[Quiz Review] ReviewItem created: {get_word_text_safely(word)}")
        return review_item

    except Exception as e:
        print(f"[Quiz Review] Failed to create ReviewItem for {get_word_text_safely(word)}: {e}")
        return None


def create_vocabulary_practice_log(user, word, user_answer, correct_answer, is_correct):
    """
    Create VocabularyPracticeLog.

    This is important because srs.review_list() filters out words
    that do not have VocabularyPracticeLog.
    """

    if not user or not word:
        return None

    try:
        log = VocabularyPracticeLog(
            user=user,
            word=word,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            cefr_level_at_time=getattr(user, "cefr_level", "A1"),
            practiced_at=datetime.utcnow()
        )
        log.save()

        print(f"[Quiz Review] VocabularyPracticeLog created: {get_word_text_safely(word)}")
        return log

    except Exception as e:
        print(f"[Quiz Review] Failed to create VocabularyPracticeLog for {get_word_text_safely(word)}: {e}")
        return None


def add_quiz_word_to_review(user, target_word, user_answer, correct_answer, is_correct):
    """
    Add every quiz target word to Vocabulary Review.

    Required by your current SRS design:
    1. ReviewItem must exist.
    2. VocabularyPracticeLog must exist.

    Without VocabularyPracticeLog, review_list() will hide the word.

    Repeating quiz:
    - does NOT overwrite ReviewItem
    - creates a new VocabularyPracticeLog every time
    """

    if not user or not target_word:
        print("[Quiz Review] Missing user or target_word.")
        return False

    word = get_word_by_text(target_word)

    if not word:
        return False

    review_item = create_or_get_review_item(user, word)

    if not review_item:
        return False

    practice_log = create_vocabulary_practice_log(
        user=user,
        word=word,
        user_answer=user_answer,
        correct_answer=correct_answer,
        is_correct=is_correct
    )

    if not practice_log:
        return False

    print(f"[Quiz Review] SUCCESS: added to review list: {get_word_text_safely(word)}")
    return True


def normalize_quiz_options(options):
    """
    Normalize quiz options to exactly 4 strings.
    """

    cleaned_options = []

    for option in options:
        if option is None:
            cleaned_options.append("")
        else:
            cleaned_options.append(option.strip())

    while len(cleaned_options) < 4:
        cleaned_options.append("")

    return cleaned_options[:4]


# ============================================================
# General / Admin routes
# ============================================================

@course_bp.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "student":
            return redirect(url_for("course.student_course_dashboard"))

        return redirect(url_for("course.admin_course_dashboard"))

    return redirect(url_for("auth.login"))


@course_bp.route("/admin/dashboard")
@login_required
def admin_course_dashboard():
    if current_user.role != "admin":
        return "Unauthorized", 403

    active_paths_count = LearningPath.objects.count()
    pending_reports_count = Report.objects(status="pending").count()

    path_form = CreatePathForm()
    chapter_form = AddChapterForm()
    unit_form = AddUnitForm()

    all_paths = LearningPath.objects.all()

    return render_template(
        "admin_course.html",
        paths=all_paths,
        path_form=path_form,
        chapter_form=chapter_form,
        unit_form=unit_form,
        active_paths_count=active_paths_count,
        pending_reports_count=pending_reports_count
    )


@course_bp.route("/admin/create-path", methods=["POST"])
@login_required
def create_path():
    if current_user.role != "admin":
        return "Unauthorized", 403

    title = request.form.get("title", "").strip()

    if not title:
        flash("Path title cannot be empty.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    path = LearningPath(path_name=title)
    path.save()

    flash("Learning path created successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-path", methods=["POST"])
@login_required
def update_path():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    new_name = request.form.get("new_name", "").strip()

    if not path_id or not new_name:
        flash("Path update failed.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    path = LearningPath.objects.get(id=path_id)
    path.path_name = new_name
    path.save()

    flash("Path updated successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/delete-path", methods=["POST"])
@login_required
def delete_path():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")

    if not path_id:
        flash("Missing path id.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    path = LearningPath.objects(id=path_id).first()

    if not path:
        flash("Path not found.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    for chapter in path.chapters:
        for unit in chapter.units:
            Progress.objects(unit=unit).delete()
            unit.delete()

        ChapterQuizAttempt.objects(chapter=chapter).delete()
        chapter.delete()

    path.delete()

    flash("Path deleted successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


# ============================================================
# Chapter management
# ============================================================

@course_bp.route("/admin/add-chapter", methods=["POST"])
@login_required
def add_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    title = request.form.get("title", "").strip()

    if not path_id or not title:
        flash("Chapter title cannot be empty.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    path = LearningPath.objects.get(id=path_id)

    chapter = Chapter(
        title=title,
        unlock_rule_type="none",
        unlock_threshold=0,
        unlock_rules=[],
        quiz_questions=[]
    )
    chapter.save()

    path.chapters.append(chapter)
    path.save()

    flash("Chapter added successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-chapter", methods=["POST"])
@login_required
def update_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form.get("chapter_id")
    new_title = request.form.get("new_title", "").strip()

    if not chapter_id or not new_title:
        flash("Chapter update failed.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    chapter = Chapter.objects.get(id=chapter_id)
    chapter.title = new_title
    chapter.save()

    flash("Chapter updated successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/delete-chapter", methods=["POST"])
@login_required
def delete_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    chapter_id = request.form.get("chapter_id")

    if not path_id or not chapter_id:
        flash("Missing path id or chapter id.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    path = LearningPath.objects.get(id=path_id)
    chapter = Chapter.objects.get(id=chapter_id)

    path.chapters = [
        existing_chapter
        for existing_chapter in path.chapters
        if str(existing_chapter.id) != str(chapter.id)
    ]
    path.save()

    for unit in chapter.units:
        Progress.objects(unit=unit).delete()
        unit.delete()

    ChapterQuizAttempt.objects(chapter=chapter).delete()
    chapter.delete()

    flash("Chapter deleted successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/edit-chapter/<chapter_id>", methods=["GET", "POST"])
@login_required
def edit_chapter(chapter_id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter = Chapter.objects.get(id=chapter_id)

    if request.method == "POST":
        chapter.title = request.form.get("title", "").strip()

        required_level = request.form.get("required_level", "0").strip()
        required_score = request.form.get("required_score", "0").strip()
        required_cefr = request.form.get("required_cefr", "").strip()

        unlock_rules = []

        if required_level and required_level != "0":
            unlock_rules.append(
                UnlockRule(
                    rule_type="level",
                    value=required_level
                )
            )

        if required_score and required_score != "0":
            unlock_rules.append(
                UnlockRule(
                    rule_type="score",
                    value=required_score
                )
            )

        if required_cefr:
            unlock_rules.append(
                UnlockRule(
                    rule_type="cefr",
                    value=required_cefr
                )
            )

        chapter.unlock_rules = unlock_rules

        # Keep legacy fields for compatibility.
        chapter.unlock_rule_type = "none"
        chapter.unlock_threshold = 0

        chapter.save()

        flash("Chapter updated successfully.", "success")
        return redirect(url_for("course.edit_chapter", chapter_id=chapter.id))

    return render_template(
        "edit_chapter.html",
        chapter=chapter
    )


# ============================================================
# Unit management
# ============================================================

@course_bp.route("/admin/add-unit", methods=["POST"])
@login_required
def add_unit():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form.get("chapter_id")
    title = request.form.get("title", "").strip()

    if not chapter_id or not title:
        flash("Unit title cannot be empty.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    chapter = Chapter.objects.get(id=chapter_id)

    unit = Unit(
        title=title,
        content=""
    )
    unit.save()

    chapter.units.append(unit)
    chapter.save()

    flash("Unit added successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-unit-title", methods=["POST"])
@login_required
def update_unit_title():
    if current_user.role != "admin":
        return "Unauthorized", 403

    unit_id = request.form.get("unit_id")
    new_title = request.form.get("new_title", "").strip()

    if not unit_id or not new_title:
        flash("Unit update failed.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    unit = Unit.objects.get(id=unit_id)
    unit.title = new_title
    unit.save()

    flash("Unit title updated successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/delete-unit", methods=["POST"])
@login_required
def delete_unit():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form.get("chapter_id")
    unit_id = request.form.get("unit_id")

    if not chapter_id or not unit_id:
        flash("Missing chapter id or unit id.", "danger")
        return redirect(url_for("course.admin_course_dashboard"))

    chapter = Chapter.objects.get(id=chapter_id)
    unit = Unit.objects.get(id=unit_id)

    chapter.units = [
        existing_unit
        for existing_unit in chapter.units
        if str(existing_unit.id) != str(unit.id)
    ]
    chapter.save()

    Progress.objects(unit=unit).delete()
    unit.delete()

    flash("Unit deleted successfully.", "success")
    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/edit-unit/<unit_id>", methods=["GET", "POST"])
@login_required
def edit_unit(unit_id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    unit = Unit.objects.get(id=unit_id)

    if request.method == "POST":
        content = request.form.get("content", "")
        unit.content = content
        unit.save()

        flash("Unit updated successfully.", "success")
        return redirect(url_for("course.edit_unit", unit_id=unit.id))

    path_index = get_path_index_by_unit(unit)

    vocabulary_entries = []

    try:
        vocabulary_entries = course_vocabulary_service.get_vocabulary_entries_from_content(
            content=unit.content or "",
            path_index=path_index,
            count=8
        )
    except Exception as e:
        print(f"[Course Vocabulary] Extraction failed: {e}")
        vocabulary_entries = []

    return render_template(
        "edit_unit.html",
        unit=unit,
        vocabulary_entries=vocabulary_entries,
        path_index=path_index
    )


# ============================================================
# Chapter quiz admin routes
# ============================================================

@course_bp.route("/admin/chapter/<chapter_id>/quiz", methods=["GET", "POST"])
@login_required
def edit_chapter_quiz(chapter_id):
    """
    Admin can save incomplete quiz drafts.
    Quiz Ready is determined by Chapter.is_quiz_ready().
    """

    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter = Chapter.objects.get(id=chapter_id)

    if request.method == "POST":
        quiz_questions = []

        for i in range(1, 6):
            question = request.form.get(f"question_{i}", "").strip()
            options = normalize_quiz_options([
                request.form.get(f"option_{i}_a", "").strip(),
                request.form.get(f"option_{i}_b", "").strip(),
                request.form.get(f"option_{i}_c", "").strip(),
                request.form.get(f"option_{i}_d", "").strip(),
            ])
            answer = request.form.get(f"answer_{i}", "").strip()
            target_word = request.form.get(f"target_word_{i}", "").strip()
            explanation = request.form.get(f"explanation_{i}", "").strip()

            quiz_questions.append(
                QuizQuestion(
                    question=question,
                    options=options,
                    answer=answer,
                    target_word=target_word,
                    explanation=explanation
                )
            )

        chapter.quiz_questions = quiz_questions
        chapter.save()

        if chapter.is_quiz_ready():
            flash("Quiz saved. Status: Quiz Ready.", "success")
        else:
            flash("Quiz draft saved. Complete all 5 questions to make it Quiz Ready.", "warning")

        return redirect(url_for("course.edit_chapter_quiz", chapter_id=chapter_id))

    return render_template(
        "edit_chapter_quiz.html",
        chapter=chapter
    )


# ============================================================
# Student routes
# ============================================================

@course_bp.route("/student/dashboard")
@login_required
@no_cache
def student_course_dashboard():
    if current_user.role != "student":
        return "Unauthorized", 403

    try:
        user_leaderboard = leaderboard_service.get_user_leaderboard(limit=10)
    except Exception as e:
        print(f"[Dashboard] Leaderboard failed: {e}")
        user_leaderboard = []

    return render_template(
        "student_dashboard.html",
        user=current_user,
        user_leaderboard=user_leaderboard
    )


@course_bp.route("/student/settings/cefr", methods=["GET", "POST"])
@login_required
def student_cefr_setting():
    if current_user.role != "student":
        return "Unauthorized", 403

    cefr_levels = [
        {
            "value": "A1",
            "title": "A1 Beginner",
            "description": "I can understand basic words and simple phrases."
        },
        {
            "value": "A2",
            "title": "A2 Elementary",
            "description": "I can understand simple everyday sentences."
        },
        {
            "value": "B1",
            "title": "B1 Intermediate",
            "description": "I can understand common topics and basic articles."
        },
        {
            "value": "B2",
            "title": "B2 Upper-Intermediate",
            "description": "I can understand more complex texts and discussions."
        },
        {
            "value": "C1",
            "title": "C1 Advanced",
            "description": "I can understand advanced academic or professional English."
        },
        {
            "value": "C2",
            "title": "C2 Proficient",
            "description": "I can understand almost everything with ease."
        },
    ]

    if request.method == "POST":
        selected_level = request.form.get("cefr_level")
        allowed_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

        if selected_level not in allowed_levels:
            flash("Invalid CEFR level.", "danger")
            return redirect(url_for("course.student_cefr_setting"))

        current_user.cefr_level = selected_level
        current_user.save()

        flash("Your English level has been updated.", "success")
        return redirect(url_for("course.student_course_dashboard"))

    return render_template(
        "student_cefr_setting.html",
        user=current_user,
        cefr_levels=cefr_levels
    )


@course_bp.route("/student/courses")
@login_required
def student_learning_paths():
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    all_paths = LearningPath.objects.all()

    latest_attempt_map = {}
    best_score_map = {}
    unit_access_map = {}
    unit_completed_map = {}
    quiz_access_map = {}
    chapter_unlock_map = {}

    for path in all_paths:
        for chapter in path.chapters:
            chapter_unlock_map[str(chapter.id)] = check_chapter_unlocked(
                user,
                chapter
            )

            latest_attempt = ChapterQuizAttempt.objects(
                student=user,
                chapter=chapter
            ).order_by("-created_at").first()

            best_attempt = ChapterQuizAttempt.objects(
                student=user,
                chapter=chapter
            ).order_by("-score").first()

            latest_attempt_map[str(chapter.id)] = latest_attempt
            best_score_map[str(chapter.id)] = best_attempt.score if best_attempt else None

            quiz_access_map[str(chapter.id)] = can_take_chapter_quiz(
                user,
                chapter
            )

            for unit in chapter.units:
                unit_access_map[str(unit.id)] = can_access_unit(
                    user,
                    chapter,
                    unit
                )

                unit_completed_map[str(unit.id)] = has_completed_unit(
                    user,
                    unit
                )

    return render_template(
        "student_course.html",
        paths=all_paths,
        user=user,
        latest_attempt_map=latest_attempt_map,
        best_score_map=best_score_map,
        unit_access_map=unit_access_map,
        unit_completed_map=unit_completed_map,
        quiz_access_map=quiz_access_map,
        chapter_unlock_map=chapter_unlock_map,

        # Compatibility for old template code.
        ChapterQuizAttempt=ChapterQuizAttempt
    )


@course_bp.route("/student/unit/<unit_id>")
@login_required
def view_unit(unit_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    unit = Unit.objects.get(id=unit_id)
    chapter = get_chapter_by_unit(unit)

    if not chapter:
        flash("Cannot find chapter for this unit.", "danger")
        return redirect(url_for("course.student_learning_paths"))

    if not check_chapter_unlocked(user, chapter):
        flash("This chapter is locked.", "warning")
        return redirect(url_for("course.student_learning_paths"))

    if not can_access_unit(user, chapter, unit):
        flash("Please complete the previous unit first.", "warning")
        return redirect(url_for("course.student_learning_paths"))

    mark_unit_completed(user, unit)

    xp_gained = safe_add_xp(user, 2)
    flash(f"You gained {xp_gained} XP for studying this unit.", "success")

    path_index = get_path_index_by_unit(unit)

    highlighted_content = unit.content or ""
    vocabulary_entries = []

    try:
        result = course_vocabulary_service.process_course_content(
            content=unit.content or "",
            path_index=path_index,
            count=8
        )

        if isinstance(result, tuple):
            highlighted_content, vocabulary_entries = result
        else:
            vocabulary_entries = result

    except Exception as e:
        print(f"[Course Vocabulary] View unit process failed: {e}")

        try:
            vocabulary_entries = course_vocabulary_service.get_vocabulary_entries_from_content(
                content=unit.content or "",
                path_index=path_index,
                count=8
            )
        except Exception as inner_e:
            print(f"[Course Vocabulary] View unit extraction failed: {inner_e}")
            vocabulary_entries = []

    html_content = markdown.markdown(
        highlighted_content or "",
        extensions=["fenced_code", "tables"]
    )

    return render_template(
        "view_unit.html",
        unit=unit,
        html_content=html_content,
        vocabulary_entries=vocabulary_entries,
        path_index=path_index
    )


@course_bp.route("/student/chapter/<chapter_id>/quiz", methods=["GET", "POST"])
@login_required
def take_chapter_quiz(chapter_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    user = current_user._get_current_object()
    chapter = Chapter.objects.get(id=chapter_id)

    if not chapter.is_quiz_ready():
        flash("This chapter quiz is not ready yet.", "warning")
        return redirect(url_for("course.student_learning_paths"))

    if not can_take_chapter_quiz(user, chapter):
        flash("Please complete all units in this chapter before taking the quiz.", "warning")
        return redirect(url_for("course.student_learning_paths"))

    previous_attempts = ChapterQuizAttempt.objects(
        student=user,
        chapter=chapter
    ).order_by("-created_at")

    if request.method == "POST":
        correct_count = 0
        total = len(chapter.quiz_questions)
        answer_records = []
        results = []
        review_words_added = 0

        for index, question in enumerate(chapter.quiz_questions):
            user_answer = request.form.get(f"answer_{index}", "").strip()
            correct_answer = question.answer.strip()
            is_correct = user_answer == correct_answer

            if is_correct:
                correct_count += 1

            added = add_quiz_word_to_review(
                user=user,
                target_word=question.target_word,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct
            )

            if added:
                review_words_added += 1

            record = QuizAnswerRecord(
                question=question.question,
                target_word=question.target_word,
                user_answer=user_answer,
                correct_answer=correct_answer,
                is_correct=is_correct,
                explanation=question.explanation
            )
            answer_records.append(record)

            results.append({
                "index": index + 1,
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
            })

        score = correct_count * 20

        xp_gained = 5 + (correct_count * 2)

        if correct_count == total:
            xp_gained += 5

        safe_add_xp(user, xp_gained)

        attempt = ChapterQuizAttempt(
            student=user,
            chapter=chapter,
            score=score,
            correct_count=correct_count,
            total_questions=total,
            xp_gained=xp_gained,
            answers=answer_records
        )
        attempt.save()

        return render_template(
            "chapter_quiz_result.html",
            chapter=chapter,
            score=score,
            correct_count=correct_count,
            total=total,
            results=results,
            xp_gained=xp_gained,
            review_added_count=review_words_added,
            attempt=attempt
        )

    return render_template(
        "chapter_quiz.html",
        chapter=chapter,
        previous_attempts=previous_attempts.limit(10)
    )


# ============================================================
# Vocabulary admin routes
# ============================================================

@course_bp.route("/admin/vocabulary")
@login_required
def admin_vocabulary():
    if current_user.role != "admin":
        return "Unauthorized", 403

    try:
        vocabs = vocab_service.get_all_vocabulary()
    except Exception as e:
        print(f"[Vocabulary] get_all_vocabulary failed: {e}")
        vocabs = []

    return render_template(
        "admin_vocabulary.html",
        vocabs=vocabs
    )


@course_bp.route("/admin/vocabulary/import", methods=["POST"])
@login_required
def import_vocabulary():
    if current_user.role != "admin":
        return "Unauthorized", 403

    if "file" not in request.files:
        flash("沒有上傳檔案", "danger")
        return redirect(url_for("course.admin_vocabulary"))

    file = request.files["file"]

    if file.filename == "":
        flash("未選擇檔案", "danger")
        return redirect(url_for("course.admin_vocabulary"))

    if file and file.filename.endswith(".json"):
        try:
            count = vocab_service.import_from_json(file)
            flash(f"成功匯入 {count} 筆單字！", "success")
        except Exception as e:
            flash(f"匯入失敗: {str(e)}", "danger")
    else:
        flash("請上傳 JSON 檔案格式", "danger")

    return redirect(url_for("course.admin_vocabulary"))