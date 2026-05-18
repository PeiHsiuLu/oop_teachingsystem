from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.models.course import LearningPath, Chapter, Unit
from app.services.course_service import CourseService
from app.models.forms import CreatePathForm, AddChapterForm, AddUnitForm, EditUnitForm
from flask_login import login_required, current_user
from app.utils.decorators import no_cache
from app.services.leaderboard_service import LeaderboardService
import markdown

course_bp = Blueprint('course', __name__)
course_service = CourseService()
leaderboard_service = LeaderboardService()
@course_bp.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('course.student_course_dashboard'))
        return redirect(url_for('course.admin_course_dashboard'))
    return redirect(url_for('auth.login'))

@course_bp.route('/admin/dashboard')
@login_required
def admin_course_dashboard():
    # Instantiate the forms
    path_form = CreatePathForm()
    chapter_form = AddChapterForm()
    unit_form = AddUnitForm()
    
    all_paths = LearningPath.objects.all()
    return render_template('admin_course.html', 
                           paths=all_paths, 
                           path_form=path_form, 
                           chapter_form=chapter_form,
                           unit_form=unit_form)

@course_bp.route('/admin/create-path', methods=['POST'])
@login_required
def create_path():
    name = request.form.get('name') 
    course_service.create_learning_path(name)
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/admin/add-chapter', methods=['POST'])
@login_required
def add_chapter():
    if current_user.role != 'admin':
        return "Unauthorized", 403
        
    path_id = request.form.get('path_id')
    title = request.form.get('title')
    rule_type = request.form.get('rule_type')
    threshold = int(request.form.get('threshold', 0)) # Default to 0
    
    # Pass these to the service
    course_service.add_chapter_to_path(path_id, title, rule_type, threshold)
    
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/admin/add-unit', methods=['POST'])
@login_required
def add_unit():
    # Check if user is admin (you can check current_user.role)
    if current_user.role != 'admin':
        return "Unauthorized", 403
        
    chapter_id = request.form['chapter_id']
    title = request.form['title']
    course_service.add_unit_to_chapter(chapter_id, title, "Content goes here...")
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/admin/delete-path', methods=['POST'])
@login_required
def delete_path():
    if current_user.role != 'admin': return "Unauthorized", 403
    course_service.delete_path(request.form.get('path_id'))
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/admin/delete-chapter', methods=['POST'])
@login_required
def delete_chapter():
    if current_user.role != 'admin': return "Unauthorized", 403
    path_id = request.form.get('path_id')
    chapter_id = request.form.get('chapter_id')
    course_service.delete_chapter(path_id, chapter_id)
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/admin/edit-chapter/<chapter_id>', methods=['GET', 'POST'])
@login_required
def edit_chapter(chapter_id):
    if current_user.role != 'admin': return "Unauthorized", 403
    
    chapter = Chapter.objects.get(id=chapter_id)
    
    if request.method == 'POST':
        # Grab new values from form
        chapter.title = request.form.get('title')
        chapter.unlock_rule_type = request.form.get('rule_type')
        chapter.unlock_threshold = int(request.form.get('threshold', 0))
        chapter.save()
        flash("Chapter updated!", "success")
        return redirect(url_for('course.admin_course_dashboard'))
        
    return render_template('edit_chapter.html', chapter=chapter)

@course_bp.route('/admin/edit-unit/<unit_id>', methods=['GET', 'POST'])
@login_required
def edit_unit(unit_id):
    if current_user.role != 'admin': return "Unauthorized", 403
    
    unit = Unit.objects.get(id=unit_id)
    form = EditUnitForm(data={'content': unit.content}) # Pre-fill the form
    
    if form.validate_on_submit():
        course_service.update_unit(unit_id, form.content.data)
        flash("Unit updated successfully!", "success")
        return redirect(url_for('course.admin_course_dashboard'))
        
    return render_template('edit_unit.html', unit=unit, form=form)

@course_bp.route('/admin/delete-unit', methods=['POST'])
@login_required
def delete_unit():
    if current_user.role != 'admin': return "Unauthorized", 403
    chapter_id = request.form.get('chapter_id')
    unit_id = request.form.get('unit_id')
    course_service.delete_unit(chapter_id, unit_id)
    return redirect(url_for('course.admin_course_dashboard'))

@course_bp.route('/student/dashboard')
@login_required
@no_cache
def student_course_dashboard():
    # Only students allowed
    if current_user.role != 'student':
        return "Unauthorized", 403

    user_leaderboard = leaderboard_service.get_user_leaderboard(limit=10)
    
    return render_template(
        'student_dashboard.html',
        user=current_user,
        user_leaderboard=user_leaderboard
    )

@course_bp.route('/student/courses')
@login_required
def student_learning_paths():
    # Only students allowed
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    all_paths = LearningPath.objects.all()
    return render_template('student_course.html', paths=all_paths, user=current_user)

@course_bp.route('/student/unit/<unit_id>')
@login_required
def view_unit(unit_id):
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    unit = Unit.objects.get(id=unit_id)
    course_service.mark_unit_complete(current_user.id, unit.id)
    
    # Convert Markdown stored in database to HTML
    html_content = markdown.markdown(unit.content, extensions=['fenced_code', 'tables'])
    
    return render_template('view_unit.html', unit=unit, html_content=html_content)