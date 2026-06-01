from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.course import LearningPath, Chapter, Unit, QuizQuestion
from app.models.forms import CreatePathForm, AddChapterForm, AddUnitForm
from app.models.report import Report
from app.models.word import Word

from app.services.course_service import CourseService
from app.services.leaderboard_service import LeaderboardService
from app.services.vocabulary_service import VocabularyService
from app.services.srs_service import SRSManager, SuperMemo2Strategy
from app.services.course_vocabulary_service import CourseVocabularyService

from app.repositories.word_repository import WordRepository
from app.utils.decorators import no_cache

import markdown
import re


course_bp = Blueprint("course", __name__)

course_service = CourseService()
leaderboard_service = LeaderboardService()
vocab_service = VocabularyService()
course_vocabulary_service = CourseVocabularyService()

word_repo = WordRepository()
srs_strategy = SuperMemo2Strategy()
srs_manager = SRSManager(
    strategy=srs_strategy,
    word_repository=word_repo
)


def safe_add_xp(user, xp_amount):
    """
    Add XP to current user safely.

    Some Student models may not have add_xp().
    This function avoids AttributeError.
    """

    if not user:
        return

    if hasattr(user, "add_xp"):
        user.add_xp(xp_amount)
        return

    current_xp = getattr(user, "xp", 0)
    user.xp = current_xp + xp_amount
    user.save()


def add_word_to_review_by_text(user, target_word, was_correct=False):
    """
    Add a target word to Vocabulary Review by word_text.

    This is used when the student answers a chapter quiz question.
    Usually, wrong answers should enter review.
    """

    if not user or not target_word:
        return False

    word = Word.objects(word_text__iexact=target_word.strip()).first()

    if not word:
        return False

    try:
        srs_manager.add_word_to_review_queue(user.id, word.id)
        return True
    except Exception:
        return False


def add_course_words_to_review_queue(user, unit):
    """
    Kept for future use only.

    Currently not called, because the current design is:
    - course reading itself does not add words to review
    - vocabulary practice / quiz wrong answers add words to review
    """

    content = unit.content or ""
    added_count = 0
    max_words_to_add = 10

    for word in Word.objects():
        if added_count >= max_words_to_add:
            break

        word_text = getattr(word, "word_text", None)

        if not word_text:
            continue

        pattern = re.compile(
            rf"\b{re.escape(word_text)}(s|es)?\b",
            re.IGNORECASE
        )

        if pattern.search(content):
            srs_manager.add_word_to_review_queue(user.id, word.id)
            added_count += 1

    return added_count


def get_path_index_by_unit(unit):
    """
    Find which LearningPath this unit belongs to.
    """

    for path in LearningPath.objects.all():
        chapters = getattr(path, "chapters", [])

        for chapter in chapters:
            units = getattr(chapter, "units", [])

            for path_unit in units:
                if str(path_unit.id) == str(unit.id):
                    path_name = getattr(path, "name", "")

                    if not path_name:
                        path_name = getattr(path, "title", "")

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


def get_path_index_by_chapter(chapter):
    """
    Find which LearningPath this chapter belongs to.
    """

    for path in LearningPath.objects.all():
        chapters = getattr(path, "chapters", [])

        for path_chapter in chapters:
            if str(path_chapter.id) == str(chapter.id):
                path_name = getattr(path, "name", "")

                if not path_name:
                    path_name = getattr(path, "title", "")

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

    name = request.form.get("title")
    course_service.create_learning_path(name)

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/add-chapter", methods=["POST"])
@login_required
def add_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    title = request.form.get("title")
    rule_type = request.form.get("rule_type")
    raw_threshold = request.form.get("threshold")

    threshold = int(raw_threshold) if raw_threshold and raw_threshold.strip() else 0

    course_service.add_chapter_to_path(
        path_id,
        title,
        rule_type,
        threshold
    )

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/add-unit", methods=["POST"])
@login_required
def add_unit():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form["chapter_id"]
    title = request.form["title"]

    course_service.add_unit_to_chapter(
        chapter_id,
        title,
        "Content goes here..."
    )

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/delete-path", methods=["POST"])
@login_required
def delete_path():
    if current_user.role != "admin":
        return "Unauthorized", 403

    course_service.delete_path(request.form.get("path_id"))

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-path", methods=["POST"])
@login_required
def update_path():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    new_name = request.form.get("new_name")

    try:
        if path_id and new_name:
            course_service.update_path(path_id, new_name)
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-chapter", methods=["POST"])
@login_required
def update_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form.get("chapter_id")
    new_title = request.form.get("new_title")

    try:
        if chapter_id and new_title:
            course_service.update_chapter_title(chapter_id, new_title)
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/update-unit-title", methods=["POST"])
@login_required
def update_unit_title():
    if current_user.role != "admin":
        return "Unauthorized", 403

    unit_id = request.form.get("unit_id")
    new_title = request.form.get("new_title")

    try:
        if unit_id and new_title:
            course_service.update_unit_title(unit_id, new_title)
    except Exception as e:
        flash(str(e), "error")

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/delete-chapter", methods=["POST"])
@login_required
def delete_chapter():
    if current_user.role != "admin":
        return "Unauthorized", 403

    path_id = request.form.get("path_id")
    chapter_id = request.form.get("chapter_id")

    course_service.delete_chapter(path_id, chapter_id)

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/edit-chapter/<chapter_id>", methods=["GET", "POST"])
@login_required
def edit_chapter(chapter_id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter = Chapter.objects.get(id=chapter_id)

    if request.method == "POST":
        chapter.title = request.form.get("title")
        chapter.unlock_rule_type = request.form.get("rule_type")

        raw_threshold = request.form.get("threshold")
        chapter.unlock_threshold = (
            int(raw_threshold)
            if raw_threshold and raw_threshold.strip()
            else 0
        )

        chapter.save()

        flash("Chapter updated!", "success")
        return redirect(url_for("course.admin_course_dashboard"))

    return render_template(
        "edit_chapter.html",
        chapter=chapter
    )


@course_bp.route("/admin/edit-unit/<unit_id>", methods=["GET", "POST"])
@login_required
def edit_unit(unit_id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    unit = Unit.objects.get(id=unit_id)

    if request.method == "POST":
        content = request.form.get("content", "")

        course_service.update_unit(unit_id, content)

        flash("Unit updated successfully!", "success")
        return redirect(url_for("course.admin_course_dashboard"))

    path_index = get_path_index_by_unit(unit)

    vocabulary_entries = course_vocabulary_service.get_vocabulary_entries_from_content(
        content=unit.content,
        path_index=path_index,
        count=8
    )

    return render_template(
        "edit_unit.html",
        unit=unit,
        vocabulary_entries=vocabulary_entries,
        path_index=path_index
    )


@course_bp.route("/admin/delete-unit", methods=["POST"])
@login_required
def delete_unit():
    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter_id = request.form.get("chapter_id")
    unit_id = request.form.get("unit_id")

    course_service.delete_unit(chapter_id, unit_id)

    return redirect(url_for("course.admin_course_dashboard"))


@course_bp.route("/admin/chapter/<chapter_id>/quiz", methods=["GET", "POST"])
@login_required
def edit_chapter_quiz(chapter_id):
    """
    Admin page for editing a Chapter vocabulary quiz.

    Each Chapter has 5 vocabulary multiple-choice questions.
    """

    if current_user.role != "admin":
        return "Unauthorized", 403

    chapter = Chapter.objects.get(id=chapter_id)

    if request.method == "POST":
        quiz_questions = []

        for i in range(1, 6):
            question = request.form.get(f"question_{i}", "").strip()
            option_a = request.form.get(f"option_{i}_a", "").strip()
            option_b = request.form.get(f"option_{i}_b", "").strip()
            option_c = request.form.get(f"option_{i}_c", "").strip()
            option_d = request.form.get(f"option_{i}_d", "").strip()
            answer = request.form.get(f"answer_{i}", "").strip()
            target_word = request.form.get(f"target_word_{i}", "").strip()
            explanation = request.form.get(f"explanation_{i}", "").strip()

            options = [option_a, option_b, option_c, option_d]

            # Skip completely empty question blocks.
            if not question and not any(options):
                continue

            if not question or not all(options) or answer not in options:
                flash(
                    f"Question {i} is incomplete or the answer does not match any option.",
                    "danger"
                )
                return redirect(url_for("course.edit_chapter_quiz", chapter_id=chapter_id))

            quiz_questions.append(
                QuizQuestion(
                    question=question,
                    options=options,
                    answer=answer,
                    target_word=target_word,
                    explanation=explanation
                )
            )

        if len(quiz_questions) != 5:
            flash("Each chapter quiz must contain exactly 5 questions.", "danger")
            return redirect(url_for("course.edit_chapter_quiz", chapter_id=chapter_id))

        chapter.quiz_questions = quiz_questions
        chapter.save()

        flash("Chapter vocabulary quiz updated successfully!", "success")
        return redirect(url_for("course.admin_course_dashboard"))

    return render_template(
        "edit_chapter_quiz.html",
        chapter=chapter
    )


@course_bp.route("/student/dashboard")
@login_required
@no_cache
def student_course_dashboard():
    if current_user.role != "student":
        return "Unauthorized", 403

    user_leaderboard = leaderboard_service.get_user_leaderboard(limit=10)

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
        }
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

    all_paths = LearningPath.objects.all()

    return render_template(
        "student_course.html",
        paths=all_paths,
        user=current_user
    )


@course_bp.route("/student/unit/<unit_id>")
@login_required
def view_unit(unit_id):
    if current_user.role != "student":
        return "Unauthorized", 403

    unit = Unit.objects.get(id=unit_id)

    course_service.mark_unit_complete(current_user.id, unit.id)

    path_index = get_path_index_by_unit(unit)

    highlighted_content, vocabulary_entries = course_vocabulary_service.process_course_content(
        content=unit.content,
        path_index=path_index,
        count=8
    )

    html_content = markdown.markdown(
        highlighted_content,
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
    """
    Student takes a chapter vocabulary quiz.

    Wrong target_words are added to Vocabulary Review.
    """

    if current_user.role != "student":
        return "Unauthorized", 403

    chapter = Chapter.objects.get(id=chapter_id)

    if not chapter.quiz_questions or len(chapter.quiz_questions) == 0:
        flash("This chapter does not have a vocabulary quiz yet.", "warning")
        return redirect(url_for("course.student_learning_paths"))

    if request.method == "POST":
        score = 0
        total = len(chapter.quiz_questions)
        results = []
        wrong_words_added = 0

        for index, question in enumerate(chapter.quiz_questions):
            user_answer = request.form.get(f"answer_{index}", "").strip()
            correct_answer = question.answer

            is_correct = user_answer == correct_answer

            if is_correct:
                score += 1
            else:
                added = add_word_to_review_by_text(
                    user=current_user,
                    target_word=question.target_word,
                    was_correct=False
                )

                if added:
                    wrong_words_added += 1

            results.append({
                "index": index + 1,
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })

        # XP rule:
        # Complete quiz: +5 XP
        # Each correct answer: +2 XP
        xp_gained = 5 + (score * 2)
        safe_add_xp(current_user, xp_gained)

        return render_template(
            "chapter_quiz_result.html",
            chapter=chapter,
            score=score,
            total=total,
            results=results,
            xp_gained=xp_gained,
            wrong_words_added=wrong_words_added
        )

    return render_template(
        "chapter_quiz.html",
        chapter=chapter
    )


@course_bp.route("/admin/vocabulary")
@login_required
def admin_vocabulary():
    if current_user.role != "admin":
        return "Unauthorized", 403

    vocabs = vocab_service.get_all_vocabulary()

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