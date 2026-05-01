from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.game_service import GameManager

game_bp = Blueprint("game", __name__)
game_manager = GameManager()


@game_bp.route("/api/game/event", methods=["POST"])
@login_required
def process_game_event():
    data = request.json
    event = game_manager.process_event(
        event_type=data.get("event_type"),
        user_id=current_user.id,
        data=data
    )

    if not event:
        return jsonify({"error": "Failed to process event"}), 400

    return jsonify({
        "message": "Game event processed",
        "points": event.points,
        "event_type": event.event_type
    }), 200