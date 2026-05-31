import random
import re
from app.models.word import Word


class VocabularyPracticeService:
    CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

    def choose_target_level(self, user_level):
        """
        Choose a word difficulty level based on the user's current CEFR level.
        Most of the time, use the current level.
        Sometimes, use one level easier or harder.
        """

        if user_level not in self.CEFR_LEVELS:
            user_level = "A1"

        current_index = self.CEFR_LEVELS.index(user_level)
        weighted_levels = []

        # Easier level
        if current_index - 1 >= 0:
            weighted_levels += [self.CEFR_LEVELS[current_index - 1]] * 15

        # Current level
        weighted_levels += [user_level] * 70

        # Harder level
        if current_index + 1 < len(self.CEFR_LEVELS):
            weighted_levels += [self.CEFR_LEVELS[current_index + 1]] * 15

        return random.choice(weighted_levels)

    def get_random_word_by_level(self, user_level):
        """
        Get a random word from the database based on CEFR level.
        """

        target_level = self.choose_target_level(user_level)

        words = Word.objects(
            difficulty_level=target_level,
            example_sentences__exists=True,
            example_sentences__not__size=0
        )

        # fallback: use current level if target level has no data
        if words.count() == 0:
            words = Word.objects(
                difficulty_level=user_level,
                example_sentences__exists=True,
                example_sentences__not__size=0
            )

        if words.count() == 0:
            return None

        return random.choice(list(words))

    def build_word_hint(self, matched_text):
        """
        Build a hint from the actual word found in the sentence.

        Examples:
        shoe   -> s__e
        shoes  -> s___s
        Enough -> E____h
        """

        source_text = matched_text.strip()

        if len(source_text) == 0:
            return "_____"

        if len(source_text) == 1:
            return source_text

        if len(source_text) == 2:
            return source_text[0] + "_"

        return source_text[0] + ("_" * (len(source_text) - 2)) + source_text[-1]

    def find_word_in_sentence(self, word_text, sentence):
        """
        Find the target word in the sentence.

        This function supports simple plural forms:
        shoe  -> shoe / shoes
        class -> class / classes

        It returns the actual matched word in the sentence.
        """

        word_text = word_text.strip()

        candidate_patterns = [
            rf"\b{re.escape(word_text)}es\b",
            rf"\b{re.escape(word_text)}s\b",
            rf"\b{re.escape(word_text)}\b"
        ]

        for pattern_text in candidate_patterns:
            pattern = re.compile(pattern_text, re.IGNORECASE)
            match = pattern.search(sentence)

            if match:
                return match.group(0)

        return None

    def make_blank_sentence(self, word_text, sentence):
        """
        Replace the target word in the sentence with a hint version.

        Example:
        word_text: shoe
        sentence: I need to buy new shoes.
        result: I need to buy new s___s.
        answer: shoes
        """

        matched_word = self.find_word_in_sentence(word_text, sentence)

        if not matched_word:
            return sentence, self.build_word_hint(word_text), word_text

        hint_word = self.build_word_hint(matched_word)

        pattern = re.compile(rf"\b{re.escape(matched_word)}\b", re.IGNORECASE)
        blank_sentence = pattern.sub(hint_word, sentence, count=1)

        target_answer = matched_word.lower()

        return blank_sentence, hint_word, target_answer

    def generate_question_for_user(self, user):
        """
        Generate a fill-in-the-blank vocabulary question for the current user.
        """

        user_level = getattr(user, "cefr_level", "A1")
        word = self.get_random_word_by_level(user_level)

        if not word:
            return None

        sentence = random.choice(word.example_sentences)

        blank_sentence, hint_word, target_answer = self.make_blank_sentence(
            word.word_text,
            sentence
        )

        return {
            "word_id": str(word.id),
            "word_text": word.word_text,
            "definition": word.definition,
            "part_of_speech": word.part_of_speech,
            "difficulty_level": word.difficulty_level,
            "example_sentence": sentence,
            "blank_sentence": blank_sentence,
            "hint_word": hint_word,
            "target_answer": target_answer
        }

    def check_answer(self, correct_answer, user_answer):
        """
        Check whether the user's answer is correct.
        """

        if not user_answer:
            return False

        return correct_answer.strip().lower() == user_answer.strip().lower()