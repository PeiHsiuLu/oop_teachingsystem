from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.dialogue_engine import DialogueEngine
from app.models.dialogue import DialogueNode
from app.utils.decorators import role_required

dialogue_bp = Blueprint('dialogue', __name__)
dialogue_engine = DialogueEngine()

@dialogue_bp.route('/student/dialogue', methods=['GET'])
@login_required
def student_dialogue_page():
    """Renders the Scenario Dialogue Play page (UC4)."""
    if current_user.role != 'student':
        return "Unauthorized", 403

    return render_template('student_dialogue.html')

@dialogue_bp.route('/api/dialogue/start', methods=['POST'])
@login_required
def start_dialogue():
    """API endpoint to start a new dialogue session."""
    data = request.json
    scenario_id = data.get('scenario_id')
    print(f"API: Received request to start dialogue with scenario_id: {scenario_id}")
    try:
        session_data = dialogue_engine.start_session(current_user.id, scenario_id)
        return jsonify(session_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@dialogue_bp.route('/api/dialogue/choice', methods=['POST'])
@login_required
def handle_choice():
    """API endpoint to process a user's choice and get the next node."""
    data = request.json
    node_id = data.get('node_id')
    option_index = data.get('option_index')
    try:
        next_node_data = dialogue_engine.handle_user_choice(node_id, option_index)
        return jsonify(next_node_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@dialogue_bp.route('/api/admin/dialogue/create', methods=['POST'])
@login_required
@role_required('admin')
def create_dialogue_node():
    """API endpoint for Admins to create a new dialogue node (UC4_3)."""
    data = request.json
    node_id = data.get('node_id')
    npc_text = data.get('npc_text')
    options = data.get('options', [])
    
    try:
        dialogue_engine.create_node(node_id, npc_text, options)
        return jsonify({"message": f"Dialogue node '{node_id}' created successfully."}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@dialogue_bp.route('/api/dialogue/finish', methods=['POST'])
@login_required
def finish_dialogue():
    """API endpoint to finalize the dialogue, save the log, and grant XP."""
    # Passing dummy metrics for practice score and time_spent
    log = dialogue_engine.finalize_session(current_user.id, unit_id=None, score=85, time_spent=120, options_clicked=[])
    return jsonify({"message": "Dialogue finalized", "log_id": str(log.id)}), 200

@dialogue_bp.route('/api/dialogue/seed', methods=['GET'])
@login_required
def seed_dialogue_data():
    """Seeds a simple dialogue scenario for testing UC4."""
    DialogueNode.objects(node_id__startswith='test_').delete()
    DialogueNode.objects(node_id='restaurant_order_start').delete()

    node_end = DialogueNode(node_id='test_end', npc_text="Very good. This concludes our practice session.", list_of_options=[]).save()
    node2 = DialogueNode(node_id='test_order_food', npc_text="Excellent choice. We have pizza or pasta. What would you like?", list_of_options=[
        {"text": "I'll have the pizza.", "next_node_id": "test_end"},
        {"text": "I'll have the pasta.", "next_node_id": "test_end"}
    ]).save()
    node1 = DialogueNode(node_id='restaurant_order_start', npc_text="Hello! Welcome to the English Practice center. What would you like to practice today?", list_of_options=[
        {"text": "I want to practice ordering food.", "next_node_id": "test_order_food"},
        {"text": "I need directions to the train station.", "next_node_id": "test_end"}
    ]).save()

    return jsonify({"message": "Dialogue data seeded successfully. You can now start the dialogue scenario."}), 200