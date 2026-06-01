import re

from app.models.word import Word
from app.services.gemini_vocabulary_service import GeminiVocabularyService


class CourseVocabularyService:
    """
    Course vocabulary helper.

    Flow:
    1. Extract words that actually appear in the lesson.
    2. Match them with Word database.
    3. Filter common stop words.
    4. Build candidate words.
    5. Ask Gemini to select pedagogically useful words.
    6. If Gemini fails, fallback to rule-based CEFR sorting.
    """

    CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

    PATH_LEVEL_MAP = {
        1: "A1",
        2: "A2",
        3: "B1",
        4: "B2",
        5: "C1"
    }

    STOP_WORDS = {
        # Articles
        "a", "an", "the",

        # Pronouns
        "i", "you", "he", "she", "it", "we", "they",
        "me", "him", "her", "us", "them",
        "my", "your", "his", "our", "their",
        "mine", "yours", "hers", "ours", "theirs",

        # Be verbs / auxiliary verbs
        "am", "is", "are", "was", "were",
        "be", "been", "being",
        "do", "does", "did",
        "have", "has", "had",
        "can", "could", "will", "would", "shall", "should",
        "may", "might", "must",

        # Demonstratives
        "this", "that", "these", "those",

        # Common adverbs / location words
        "here", "there", "then", "now",
        "very", "so", "too", "also", "just",

        # Prepositions
        "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "over", "under", "into", "out",
        "up", "down", "about", "after", "before",

        # Conjunctions
        "and", "or", "but", "because", "if", "when", "while",

        # Conversation fillers / too common words
        "yes", "no", "please", "thank", "thanks",
        "hello", "hi", "good", "morning", "afternoon", "evening",
        "okay", "ok", "fine", "sure",

        # Too common general verbs
        "go", "get", "make", "take", "see", "look", "like",
        "want", "need", "know", "think", "say", "tell",
        "come", "find", "give", "use",

        # Contraction fragments
        "s", "t", "m", "re", "ve", "ll", "d"
    }

    IMPORTANT_PARTS_OF_SPEECH = {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "phrase",
        "phrasal verb",
        "idiom"
    }

    def __init__(self):
        self.gemini_service = GeminiVocabularyService()

    def get_target_level_by_path_index(self, path_index):
        """
        Decide the main CEFR level for a learning path.

        Path 1 -> A1
        Path 2 -> A2
        Path 3 -> B1
        Path 4 -> B2
        Path 5 -> C1
        """

        return self.PATH_LEVEL_MAP.get(path_index, "A1")

    def normalize_token(self, token):
        """
        Normalize English token.

        Examples:
        Tickets -> ticket
        bags -> bag
        stories -> story

        This is only a simple demo-level normalization.
        """

        if not token:
            return ""

        token = token.lower().strip()
        token = token.replace("’", "'")

        if "'" in token:
            token = token.split("'")[0]

        if len(token) > 4 and token.endswith("ies"):
            return token[:-3] + "y"

        if len(token) > 4 and token.endswith("es"):
            return token[:-2]

        if len(token) > 3 and token.endswith("s"):
            return token[:-1]

        return token

    def extract_tokens_from_content(self, content):
        """
        Extract English words from lesson content while preserving order.
        """

        if not content:
            return []

        raw_tokens = re.findall(r"[A-Za-z][A-Za-z\-']*", content)

        tokens = []
        seen = set()

        for raw_token in raw_tokens:
            normalized = self.normalize_token(raw_token)

            if not normalized:
                continue

            if len(normalized) <= 2:
                continue

            if normalized in self.STOP_WORDS:
                continue

            if normalized not in seen:
                tokens.append(normalized)
                seen.add(normalized)

        return tokens

    def find_word_in_database(self, token):
        """
        Find a word in the Word collection.

        Only returns a word if word_text matches the token.
        """

        return Word.objects(word_text__iexact=token).first()

    def is_good_vocabulary_candidate(self, word):
        """
        Decide whether a matched word is suitable as a candidate.

        This is only the first filter.
        Gemini will do the final selection if available.
        """

        if not word:
            return False

        word_text = getattr(word, "word_text", "")
        definition = getattr(word, "definition", "")
        part_of_speech = getattr(word, "part_of_speech", "")
        example_sentences = getattr(word, "example_sentences", [])

        if not word_text:
            return False

        normalized_word = word_text.strip().lower()

        if normalized_word in self.STOP_WORDS:
            return False

        if len(normalized_word) <= 2:
            return False

        if not definition:
            return False

        # Because you want Air Classroom style vocabulary cards,
        # words without example sentences are not suitable.
        if not example_sentences or len(example_sentences) == 0:
            return False

        if part_of_speech:
            normalized_pos = part_of_speech.strip().lower()

            if normalized_pos in {
                "article",
                "indefinite article",
                "definite article",
                "pronoun",
                "preposition",
                "conjunction",
                "determiner",
                "auxiliary verb",
                "modal verb"
            }:
                return False

        return True

    def extract_words_from_content(self, content):
        """
        Only return words that:
        1. actually appear in the lesson content
        2. exist in the Word database
        3. pass basic vocabulary usefulness filters
        """

        tokens = self.extract_tokens_from_content(content)

        matched_words = []
        used_word_texts = set()

        for token in tokens:
            word = self.find_word_in_database(token)

            if not word:
                continue

            if not self.is_good_vocabulary_candidate(word):
                continue

            word_text = word.word_text.strip().lower()

            if word_text in used_word_texts:
                continue

            matched_words.append(word)
            used_word_texts.add(word_text)

        return matched_words

    def score_word_by_level(self, word, target_level):
        """
        Score a word according to how suitable it is for the current path level.

        Higher score means the word appears earlier in fallback mode.
        """

        score = 0

        word_level = getattr(word, "difficulty_level", "A1")
        part_of_speech = getattr(word, "part_of_speech", "")
        word_text = getattr(word, "word_text", "")

        if word_level == target_level:
            score += 100

        elif target_level in self.CEFR_LEVELS and word_level in self.CEFR_LEVELS:
            target_index = self.CEFR_LEVELS.index(target_level)
            word_index = self.CEFR_LEVELS.index(word_level)
            distance = abs(target_index - word_index)

            if distance == 1:
                score += 70
            elif distance == 2:
                score += 40
            else:
                score += 10

        else:
            score += 10

        normalized_pos = part_of_speech.strip().lower() if part_of_speech else ""

        if normalized_pos == "noun":
            score += 25
        elif normalized_pos == "verb":
            score += 20
        elif normalized_pos == "adjective":
            score += 18
        elif normalized_pos == "adverb":
            score += 12
        elif normalized_pos in {"phrase", "phrasal verb", "idiom"}:
            score += 30

        if len(word_text) >= 5:
            score += 8

        return score

    def sort_words_by_path_level(self, words, path_index):
        """
        Sort words so that words closer to the path level appear first.
        """

        target_level = self.get_target_level_by_path_index(path_index)

        return sorted(
            words,
            key=lambda word: self.score_word_by_level(word, target_level),
            reverse=True
        )

    def build_candidate_words(self, words):
        """
        Build candidate word dictionaries for Gemini.
        """

        candidates = []

        for word in words:
            example_sentence = ""

            if word.example_sentences and len(word.example_sentences) > 0:
                example_sentence = word.example_sentences[0]

            candidates.append({
                "word_text": word.word_text,
                "definition": word.definition,
                "part_of_speech": word.part_of_speech,
                "difficulty_level": word.difficulty_level,
                "example_sentence": example_sentence
            })

        return candidates

    def apply_gemini_selection(self, words, gemini_selected):
        """
        Convert Gemini selected word_text list back to Word objects.

        Returns:
        - selected_words
        - gemini_notes
        """

        if not gemini_selected:
            return words, {}

        selected_texts = []

        for item in gemini_selected:
            word_text = item.get("word_text", "").strip().lower()

            if word_text and word_text not in selected_texts:
                selected_texts.append(word_text)

        gemini_notes = {}

        for item in gemini_selected:
            word_text = item.get("word_text", "").strip().lower()

            if word_text:
                gemini_notes[word_text] = {
                    "reason": item.get("reason", ""),
                    "context_note": item.get("context_note", "")
                }

        selected_words = []

        for selected_text in selected_texts:
            for word in words:
                if word.word_text.strip().lower() == selected_text:
                    selected_words.append(word)
                    break

        if not selected_words:
            return words, {}

        return selected_words, gemini_notes

    def build_vocabulary_entries(self, words, gemini_notes=None):
        """
        Build vocabulary entries for template display.
        """

        if gemini_notes is None:
            gemini_notes = {}

        entries = []

        for word in words:
            example_sentence = ""

            if word.example_sentences and len(word.example_sentences) > 0:
                example_sentence = word.example_sentences[0]

            word_key = word.word_text.strip().lower()
            note = gemini_notes.get(word_key, {})

            entries.append({
                "word_id": str(word.id),
                "word_text": word.word_text,
                "definition": word.definition,
                "part_of_speech": word.part_of_speech,
                "difficulty_level": word.difficulty_level,
                "example_sentence": example_sentence,
                "gemini_reason": note.get("reason", ""),
                "context_note": note.get("context_note", "")
            })

        return entries

    def get_vocabulary_entries_from_content(self, content, path_index=1, count=8):
        """
        Main method for edit_unit page.

        Important:
        This method only chooses words that actually appear in the lesson content.
        It will not randomly pick unrelated words from the database.

        Gemini is used only to select from candidate words.
        If Gemini is unavailable, it falls back to rule-based sorting.
        """

        matched_words = self.extract_words_from_content(content)

        sorted_words = self.sort_words_by_path_level(
            words=matched_words,
            path_index=path_index
        )

        target_level = self.get_target_level_by_path_index(path_index)
        candidate_words = self.build_candidate_words(sorted_words)

        gemini_selected = self.gemini_service.select_vocabulary(
            lesson_content=content,
            candidate_words=candidate_words,
            target_level=target_level,
            max_words=count
        )

        selected_words, gemini_notes = self.apply_gemini_selection(
            words=sorted_words,
            gemini_selected=gemini_selected
        )

        selected_words = selected_words[:count]

        return self.build_vocabulary_entries(
            words=selected_words,
            gemini_notes=gemini_notes
        )

    def highlight_words(self, content, vocabulary_entries):
        """
        Highlight selected vocabulary words in lesson content.
        Used in the student reading page.
        """

        if not content or not vocabulary_entries:
            return content

        highlighted_content = content

        sorted_entries = sorted(
            vocabulary_entries,
            key=lambda entry: len(entry["word_text"]),
            reverse=True
        )

        for entry in sorted_entries:
            word_text = entry["word_text"]

            if not word_text:
                continue

            pattern = re.compile(
                r"\b(" + re.escape(word_text) + r"s?|es?)\b",
                re.IGNORECASE
            )

            highlighted_content = pattern.sub(
                r"<strong class='vocab-highlight'>\1</strong>",
                highlighted_content
            )

        return highlighted_content

    def process_course_content(self, content, path_index=1, count=8):
        """
        Used by student view_unit page.

        Returns:
        1. highlighted lesson content
        2. vocabulary entries
        """

        vocabulary_entries = self.get_vocabulary_entries_from_content(
            content=content,
            path_index=path_index,
            count=count
        )

        highlighted_content = self.highlight_words(
            content=content,
            vocabulary_entries=vocabulary_entries
        )

        return highlighted_content, vocabulary_entries