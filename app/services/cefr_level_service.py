class CEFRLevelService:
    CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

    # Level-up rules become stricter as the CEFR level increases.
    LEVEL_UP_RULES = {
        "A1": {
            "min_questions": 5,
            "min_accuracy": 0.8,
            "min_streak": 3
        },
        "A2": {
            "min_questions": 8,
            "min_accuracy": 0.8,
            "min_streak": 4
        },
        "B1": {
            "min_questions": 10,
            "min_accuracy": 0.85,
            "min_streak": 5
        },
        "B2": {
            "min_questions": 15,
            "min_accuracy": 0.85,
            "min_streak": 7
        },
        "C1": {
            "min_questions": 20,
            "min_accuracy": 0.9,
            "min_streak": 10
        }
    }

    def record_practice_result(self, user, is_correct):
        """
        Update user's CEFR practice statistics and check whether the user should level up.
        """

        user.cefr_total_answered += 1

        if is_correct:
            user.cefr_correct_answered += 1
            user.cefr_correct_streak += 1
        else:
            user.cefr_correct_streak = 0

        leveled_up = self.should_level_up(user)

        if leveled_up:
            self.level_up(user)
        else:
            user.save()

        return leveled_up

    def should_level_up(self, user):
        """
        Decide whether the user should move to the next CEFR level.
        Higher CEFR levels require stricter conditions.
        """

        current_level = user.cefr_level

        # C2 is already the highest CEFR level.
        if current_level == "C2":
            return False

        rule = self.LEVEL_UP_RULES.get(current_level)

        if not rule:
            return False

        if user.cefr_total_answered < rule["min_questions"]:
            return False

        accuracy = user.cefr_correct_answered / user.cefr_total_answered

        if accuracy < rule["min_accuracy"]:
            return False

        if user.cefr_correct_streak < rule["min_streak"]:
            return False

        return True

    def level_up(self, user):
        """
        Move the user to the next CEFR level and reset practice counters.
        """

        current_index = self.CEFR_LEVELS.index(user.cefr_level)
        next_level = self.CEFR_LEVELS[current_index + 1]

        user.cefr_level = next_level

        # Reset counters for the new level.
        user.cefr_total_answered = 0
        user.cefr_correct_answered = 0
        user.cefr_correct_streak = 0

        user.save()