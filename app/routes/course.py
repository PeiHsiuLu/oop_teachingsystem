from flask import Blueprint, request
from app.services.course_serivce import CourseService
from flask_login import login_required, current_user

course_bp = Blueprint('course', __name__)
course_service = CourseService()

@course_bp.route('/admin/add-unit', methods=['POST'])
@login_required
def add_unit():
    # Check if user is admin (you can check current_user.role)
    if current_user.role != 'admin':
        return "Unauthorized", 403
        
    chapter_id = request.form['chapter_id']
    title = request.form['title']
    course_service.add_unit_to_chapter(chapter_id, title, "Content goes here...")
    return "Unit added successfully!"