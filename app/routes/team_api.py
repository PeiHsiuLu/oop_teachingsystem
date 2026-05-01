from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_required
from app.services.team_service import TeamService
from app.utils.decorators import role_required

team_bp = Blueprint('team', __name__)
team_service = TeamService()

@team_bp.route('/student/teams', methods=['GET'])
@login_required
@role_required('Student') # Using your exact role decorator
def teams_dashboard():
    """Displays the Team Up dashboard where students can search or create teams."""
    all_groups = team_service.get_all_groups()
    return render_template('student_teams.html', groups=all_groups, user=current_user)

@team_bp.route('/api/teams/create', methods=['POST'])
@login_required
@role_required('Student')
def create_team():
    """API endpoint to create a new team."""
    name = request.form.get('name')
    description = request.form.get('description')
    
    try:
        team_service.create_group(name, description, current_user._get_current_object())
        flash('Team created successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'error')
        
    return redirect(url_for('team.teams_dashboard'))

@team_bp.route('/api/teams/join/<group_id>', methods=['POST'])
@login_required
@role_required('Student')
def join_team(group_id):
    """API endpoint to join a team."""
    if team_service.join_group(group_id, current_user._get_current_object()):
        flash('Successfully joined the team!', 'success')
    else:
        flash('Team not found.', 'error')
    return redirect(url_for('team.teams_dashboard'))

@team_bp.route('/api/teams/<group_id>/leaderboard', methods=['GET'])
@login_required
@role_required('Student')
def team_leaderboard(group_id):
    try:
        data = team_service.compute_leaderboard(group_id)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404