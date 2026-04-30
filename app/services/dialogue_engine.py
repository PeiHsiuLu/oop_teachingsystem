from app.models.dialogue import DialogueNode
from app.models.analytics import InteractionLog
from app.services.game_observer import GamificationObserver
import uuid

class DialogueEngine:
    """
    Service interface for managing scenario dialogue gameplay (Use Case 4).
    """
    
    def start_session(self, user_id: str, scenario_id: str):
        """UC4_1: Initializes a new dialogue session starting at a specific node."""
        print(f"DialogueEngine: Attempting to start session for user {user_id} with scenario_id: {scenario_id}")
        start_node = DialogueNode.objects(node_id=scenario_id).first()
        if not start_node:
            raise ValueError(f"Dialogue scenario '{scenario_id}' not found.")
            
        return {
            "session_id": str(uuid.uuid4()),
            "current_node": {
                "node_id": start_node.node_id,
                "npc_text": start_node.npc_text,
                "options": start_node.get_options()
            }
        }

    def handle_user_choice(self, current_node_id: str, selected_option_index: int):
        """UC4_1: Processes the student's choice and retrieves the next dialogue node."""
        node = DialogueNode.objects(node_id=current_node_id).first()
        if not node or selected_option_index >= len(node.list_of_options):
            raise ValueError("Invalid node or option selection.")
            
        selected_option = node.list_of_options[selected_option_index]
        next_node_id = selected_option.get("next_node_id") # Hidden attribute (UC4_4)
        
        next_node = DialogueNode.objects(node_id=next_node_id).first()
        if not next_node:
            return {"status": "completed", "message": "Dialogue reached an end."}
            
        return {
            "status": "ongoing",
            "current_node": {
                "node_id": next_node.node_id,
                "npc_text": next_node.npc_text,
                "options": next_node.get_options()
            }
        }

    def finalize_session(self, user_id: str, unit_id: str, score: int, time_spent: int, options_clicked: list):
        """
        UC4_2: Concludes the dialogue and saves the InteractionLog.
        """
        log = InteractionLog(
            user_id=user_id,
            unit_id=unit_id,
            correctness_score=score,
            time_spent=time_spent,
            clicked_options=options_clicked
        )
        log.save()
        
        # UC6: Gamification Observer pattern triggered
        GamificationObserver.on_task_completed(user_id, 'dialogue_finished', score)
        
        return log

    def create_node(self, node_id: str, npc_text: str, options: list):
        """UC4_3: Admin designs dialogue scripts and nodes."""
        # Check if a node with this ID already exists to prevent duplicates
        if DialogueNode.objects(node_id=node_id).first():
            raise ValueError(f"A dialogue node with ID '{node_id}' already exists.")
        
        new_node = DialogueNode(
            node_id=node_id,
            npc_text=npc_text,
            list_of_options=options
        )
        new_node.save()
        return new_node