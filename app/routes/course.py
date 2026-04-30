from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.models.course import LearningPath
from app.services.course_service import CourseService
from app.models.forms import CreatePathForm, AddChapterForm, AddUnitForm
from flask_login import login_required, current_user

course_bp = Blueprint('course', __name__)
course_service = CourseService()

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
def student_course_dashboard():
    # Only students allowed
    if current_user.role != 'student':
        return "Unauthorized", 403
    
    all_paths = LearningPath.objects.all()
    
    # We don't change the data; we just determine accessibility for the view
    return render_template('student_course.html', paths=all_paths, user=current_user)