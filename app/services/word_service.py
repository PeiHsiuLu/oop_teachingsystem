from app.models.word import Word, SentenceGeneratingRule, ReviewItem
from app.repositories.word_repository import WordRepository
from app.repositories.sentence_rule_repository import SentenceGeneratingRuleRepository
from app.repositories.user_repository import UserRepository # To get student info if needed

class WordService:
    """
    Service layer for managing words, sentence generation rules, and student review processes.
    """
    def __init__(self):
        self.word_repo = WordRepository()
        self.rule_repo = SentenceGeneratingRuleRepository()
        self.user_repo = UserRepository() # For potentially fetching student-specific data

    # --- Admin Functions ---
    def add_word(self, word_text, definition, part_of_speech, example_sentences=None, difficulty_level=1):
        """Adds a new word to the database."""
        if self.word_repo.get_by_word_text(word_text):
            raise ValueError(f"Word '{word_text}' already exists.")
        
        new_word = Word(
            word_text=word_text,
            definition=definition,
            part_of_speech=part_of_speech,
            example_sentences=example_sentences if example_sentences is not None else [],
            difficulty_level=difficulty_level
        )
        return self.word_repo.save(new_word)

    def update_word(self, word_id, **kwargs):
        """Updates an existing word."""
        word = self.word_repo.find_by_id(word_id)
        if not word:
            raise ValueError(f"Word with ID {word_id} not found.")
        
        for key, value in kwargs.items():
            if hasattr(word, key):
                setattr(word, key, value)
        return self.word_repo.save(word)

    def delete_word(self, word_id):
        """Deletes a word by ID."""
        return self.word_repo.delete(word_id)

    def get_all_words(self):
        """Retrieves all words."""
        return self.word_repo.get_all()

    def add_sentence_rule(self, rule_name, pattern, keywords=None, difficulty_level=1):
        """Adds a new sentence generation rule."""
        if self.rule_repo.get_by_rule_name(rule_name):
            raise ValueError(f"Rule '{rule_name}' already exists.")
        
        new_rule = SentenceGeneratingRule(
            rule_name=rule_name,
            pattern=pattern,
            keywords=keywords if keywords is not None else [],
            difficulty_level=difficulty_level
        )
        return self.rule_repo.save(new_rule)

    def update_sentence_rule(self, rule_id, **kwargs):
        """Updates an existing sentence generation rule."""
        rule = self.rule_repo.find_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found.")
        
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        return self.rule_repo.save(rule)

    def delete_sentence_rule(self, rule_id):
        """Deletes a sentence generation rule by ID."""
        return self.rule_repo.delete(rule_id)

    def get_all_sentence_rules(self):
        """Retrieves all sentence generation rules."""
        return self.rule_repo.get_all()

    # --- Student Functions ---
    def get_words_for_review(self, user_id, limit=10):
        """
        Selects words for a student to review based on their progress.
        This is a simplified example. A real system would use spaced repetition.
        """
        # First, try to get words the user hasn't reviewed yet
        words_to_review = self.word_repo.get_unreviewed_words_for_user(user_id, limit=limit)
        
        if not words_to_review:
            # If no new words, get words that need re-review based on mastery/last_reviewed
            words_to_review = self.word_repo.get_words_needing_review(user_id, limit=limit)

        return words_to_review

    def record_review_outcome(self, user_id, word_id, outcome):
        """
        Records the outcome of a student's review for a specific word.
        Outcome could be 'easy', 'medium', 'hard'.
        """
        return self.word_repo.update_review_item(user_id, word_id, outcome)

    def generate_sentence(self, user_id, words_to_include=None, difficulty_level=None):
        """
        Automatically creates a sentence by the situation for a student.
        This is a complex function and will be a simplified placeholder.
        """
        # 1. Determine words to use for sentence generation
        selected_words = []
        if words_to_include:
            # Fetch specific words if provided
            for w_id in words_to_include:
                word = self.word_repo.find_by_id(w_id)
                if word:
                    selected_words.append(word)
        else:
            # Otherwise, get some words the student is currently learning or needs to review
            selected_words = self.get_words_for_review(user_id, limit=3) # Get a few words

        if not selected_words:
            return "No words available to generate a sentence."

        # 2. Select appropriate sentence generation rules
        # In a real system, this would involve filtering rules by difficulty, keywords, etc.
        rules = self.rule_repo.get_all()
        
        # 3. Attempt to construct a sentence using the words and rules.
        # This is a very basic placeholder for sentence generation logic.
        # A sophisticated implementation would involve NLP, grammar parsing, etc.
        
        sentence_parts = []
        for word in selected_words:
            sentence_parts.append(word.word_text)
        
        if len(sentence_parts) > 1:
            # Example: "The student is learning: apple, banana, and orange."
            return f"The student is learning: {', '.join(sentence_parts[:-1])} and {sentence_parts[-1]}."
        elif sentence_parts:
            # Example: "The student is learning: apple."
            return f"The student is learning: {sentence_parts[0]}."
        else:
            # Fallback if no words or rules could form a sentence
            return "Could not generate a meaningful sentence with the available words and rules."

        # More advanced logic would involve:
        # - Choosing a rule based on selected_words' properties (part_of_speech, difficulty)
        # - Filling the rule's pattern with the selected words and other generic words
        # - Ensuring grammatical correctness and context