from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from datetime import datetime

from app.models.team import StudyGroup
from app.models.team_challenge import TeamChallenge


team_challenge_bp = Blueprint(
    "team_challenge",
    __name__,
    url_prefix="/team-challenge"
)


@team_challenge_bp.route("/")
@login_required
def list_challenges():
    challenges = TeamChallenge.objects().order_by("-created_at")

    valid_challenges = []

    for challenge in challenges:
        if challenge.team is None:
            continue

        if challenge.goal_type == "xp":
            total_xp = calculate_team_total_xp(challenge.team)
            challenge.update_progress(total_xp)

        valid_challenges.append(challenge)

    return render_template(
        "team_challenges.html",
        challenges=valid_challenges
    )

@team_challenge_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_challenge():
    teams = StudyGroup.objects()

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        team_id = request.form.get("team_id")
        target_value = int(request.form.get("target_value"))
        reward_xp = int(request.form.get("reward_xp", 0))
        reward_credit = int(request.form.get("reward_credit", 0))
        deadline_str = request.form.get("deadline")

        team = StudyGroup.objects(id=team_id).first()

        if not team:
            flash("Team not found.", "error")
            return redirect(url_for("team_challenge.create_challenge"))

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")

        challenge = TeamChallenge(
            title=title,
            description=description,
            team=team,
            goal_type="xp",
            target_value=target_value,
            reward_xp=reward_xp,
            reward_credit=reward_credit,
            deadline=deadline
        )

        challenge.save()

        flash("Team challenge created successfully!", "success")
        return redirect(url_for("team_challenge.list_challenges"))

    return render_template(
        "create_team_challenge.html",
        teams=teams
    )


@team_challenge_bp.route("/<challenge_id>/claim-reward")
@login_required
def claim_reward(challenge_id):
    challenge = TeamChallenge.objects(id=challenge_id).first()

    if not challenge:
        flash("Challenge not found.", "error")
        return redirect(url_for("team_challenge.list_challenges"))

    total_xp = calculate_team_total_xp(challenge.team)
    challenge.update_progress(total_xp)

    if not challenge.is_completed():
        flash("This challenge is not completed yet.", "error")
        return redirect(url_for("team_challenge.list_challenges"))

    if challenge.reward_claimed == "yes":
        flash("Reward has already been claimed.", "error")
        return redirect(url_for("team_challenge.list_challenges"))

    give_team_reward(challenge)

    challenge.reward_claimed = "yes"
    challenge.save()

    flash("Reward has been given to all team members!", "success")
    return redirect(url_for("team_challenge.list_challenges"))


def calculate_team_total_xp(team):
    total_xp = 0

    for member in team.members:
        total_xp += getattr(member, "xp", 0)

    return total_xp


def give_team_reward(challenge):
    team = challenge.team

    for member in team.members:
        if hasattr(member, "xp"):
            member.xp += challenge.reward_xp

        if hasattr(member, "credit_score"):
            member.credit_score += challenge.reward_credit

        member.save()

@team_challenge_bp.route("/create/<team_id>", methods=["GET", "POST"])
@login_required
def create_challenge_for_team(team_id):
    team = StudyGroup.objects(id=team_id).first()

    if not team:
        flash("Team not found.", "error")
        return redirect(url_for("team.teams_dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        target_value = int(request.form.get("target_value"))
        reward_xp = int(request.form.get("reward_xp", 0))
        reward_credit = int(request.form.get("reward_credit", 0))
        deadline_str = request.form.get("deadline")

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d")

        challenge = TeamChallenge(
            title=title,
            description=description,
            team=team,
            goal_type="xp",
            target_value=target_value,
            reward_xp=reward_xp,
            reward_credit=reward_credit,
            deadline=deadline
        )

        challenge.save()

        flash("Team challenge created successfully!", "success")
        return redirect(url_for("team_challenge.list_challenges"))

    return render_template(
        "create_team_challenge_for_team.html",
        team=team
    )