from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import current_user, login_required

from app.services.team_service import TeamService
from app.utils.decorators import role_required
from app.models.team_challenge import TeamChallenge


team_bp = Blueprint('team', __name__)
team_service = TeamService()


@team_bp.route('/student/teams', methods=['GET'])
@login_required
@role_required('Student')
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
        team_service.create_group(
            name,
            description,
            current_user._get_current_object()
        )
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


@team_bp.route('/api/teams/leave/<group_id>', methods=['POST'])
@login_required
@role_required('Student')
def leave_team(group_id):
    """API endpoint to leave a team."""
    try:
        if team_service.leave_group(group_id, current_user._get_current_object()):
            flash('You left the team.', 'success')
        else:
            flash('Team not found.', 'error')
    except ValueError as e:
        flash(str(e), 'error')

    return redirect(url_for('team.teams_dashboard'))


@team_bp.route('/student/teams/<group_id>', methods=['GET'])
@login_required
def team_detail(group_id):
    """Displays one team detail page, including members and team challenge progress."""
    group = team_service.get_group_by_id(group_id)

    if not group:
        flash('Team not found.', 'error')
        return redirect(url_for('team.teams_dashboard'))

    is_member = any(
        str(member.id) == str(current_user.id)
        for member in group.members
    )

    if current_user.role != "admin" and not is_member:
        flash("You are not allowed to view this team.", "error")
        return redirect(url_for('team.teams_dashboard'))

    # Get all challenges that belong to this team
    challenges = TeamChallenge.objects(team=group).order_by("-created_at")

    # Update XP challenge progress before displaying
    for challenge in challenges:
        if challenge.goal_type == "xp":
            total_xp = calculate_team_total_xp(group)
            challenge.update_progress(total_xp)

    return render_template(
        'team_detail.html',
        group=group,
        user=current_user,
        challenges=challenges
    )


@team_bp.route('/api/teams/<group_id>/leaderboard', methods=['GET'])
@login_required
@role_required('Student')
def team_leaderboard(group_id):
    """API endpoint for one team's member leaderboard."""
    try:
        data = team_service.compute_leaderboard(group_id)
        return jsonify(data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@team_bp.route('/leaderboard')
@login_required
def leaderboard():
    """Displays all teams ranked by total XP."""
    ranking = team_service.get_team_leaderboard()
    return render_template("team_leaderboard.html", ranking=ranking)


@team_bp.route('/api/teams/<group_id>/challenge/create', methods=['POST'])
@login_required
def create_challenge(group_id):
    """
    Legacy/API-style challenge creation endpoint.
    If you are already using team_challenge.create_challenge_for_team,
    this route can stay, but the button should probably use the team_challenge route.
    """
    title = request.form.get("title")
    description = request.form.get("description")
    target_xp = int(request.form.get("target_xp"))
    deadline = request.form.get("deadline")

    try:
        team_service.create_challenge(
            group_id,
            current_user._get_current_object(),
            title,
            description,
            target_xp,
            deadline
        )
        flash("Challenge created successfully!", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("team.teams_dashboard"))


def calculate_team_total_xp(group):
    """Calculate total XP of all members in a team."""
    total_xp = 0

    for member in group.members:
        total_xp += getattr(member, "xp", 0)

    return total_xp