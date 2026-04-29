from app.models.dialogue import DialogueNode

class DialogueEngine:
    """
    Handles the logic for navigating scenario-based dialogues.
    """
    def get_node(self, scenario_id: str, node_id: str) -> DialogueNode:
        """
        Fetches a specific node from the database.
        """
        node = DialogueNode.objects(scenario_id=scenario_id, node_id=node_id).first()
        if not node:
            raise ValueError(f"Node '{node_id}' not found in scenario '{scenario_id}'.")
        return node

    def start_dialogue(self, scenario_id: str) -> DialogueNode:
        """
        Gets the starting node for a given dialogue scenario.
        By convention, the starting node has a node_id of 'start'.
        """
        return self.get_node(scenario_id, 'start')

    def get_next_node(self, scenario_id: str, current_node_id: str, chosen_option_text: str) -> DialogueNode:
        current_node = self.get_node(scenario_id, current_node_id)
        for option in current_node.options:
            if option.text == chosen_option_text:
                return self.get_node(scenario_id, option.next_node_id)
        raise ValueError(f"Invalid option '{chosen_option_text}' for node '{current_node_id}'.")