from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.services.srs_manager import SRSManager

analytics_bp = Blueprint('analytics', __name__)
srs_manager = SRSManager()

@analytics_bp.route('/student/analytics', methods=['GET'])
@login_required
def student_analytics_page():
    """Renders the Result Analysis page (UC5)."""
    if current_user.role != 'student':
        return "Unauthorized", 403
        
    return render_template('student_analytics.html')

@analytics_bp.route('/api/analytics/report', methods=['GET'])
@login_required
def get_analytics_report():
    """API endpoint to fetch the student's weakness report and review strategy."""
    # 1. Get the weakness report (UC5_1)
    report = srs_manager.get_weakness_report(current_user.id)
    
    # 2. Get the review strategy (UC5_2)
    hard_words = srs_manager.schedule_review(current_user.id)
    strategy_text = "Keep it up! No severely difficult words found."
    if hard_words:
        word_list = ", ".join([w.word for w in hard_words])
        strategy_text = f"Focus your next review session on these difficult words: {word_list}."
        
    return jsonify({
        "report": report,
        "strategy": strategy_text
    }), 200