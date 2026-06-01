import json
import re

from google import genai


class GeminiVocabularyService:
    """
    Use Gemini to select pedagogically useful vocabulary words
    from candidate words that already appear in the lesson text.

    Important:
    This service does not decide candidates by itself.
    It only receives candidates from CourseVocabularyService and chooses
    which ones are most suitable for teaching.
    """

    def __init__(self):
        try:
            # The Gemini client reads GEMINI_API_KEY from environment variables.
            self.client = genai.Client()
        except Exception:
            self.client = None

    def is_available(self):
        return self.client is not None

    def build_prompt(self, lesson_content, candidate_words, target_level, max_words):
        candidate_json = json.dumps(
            candidate_words,
            ensure_ascii=False,
            indent=2
        )

        return f"""
You are an English teaching assistant designing vocabulary notes for a lesson.

Task:
Select the best vocabulary words for students from the candidate list.

Very important rules:
1. Only choose words from the candidate list.
2. The selected words must be useful for understanding this lesson.
3. Exclude overly common or function words such as good, morning, please, can, your, the, a, an.
4. Prefer topic-related words, content words, travel words, classroom-useful words, and words important for understanding the lesson.
5. Consider the target learner CEFR level: {target_level}.
6. If the word's part of speech in the candidate list does not perfectly match the lesson context, explain the contextual usage briefly in context_note.
7. Return JSON only. Do not include markdown code fences.
8. Select at most {max_words} words.
9. Do not invent words. Every selected word_text must appear in the candidate list.

Lesson content:
{lesson_content}

Candidate words:
{candidate_json}

Return format:
{{
  "selected_words": [
    {{
      "word_text": "passport",
      "reason": "Important travel document in this lesson.",
      "context_note": "Used as a noun in the airport check-in context."
    }}
  ]
}}
"""

    def parse_json_response(self, text):
        """
        Parse Gemini response into a list of selected word dictionaries.

        Expected:
        {
            "selected_words": [
                {
                    "word_text": "...",
                    "reason": "...",
                    "context_note": "..."
                }
            ]
        }
        """

        if not text:
            return []

        cleaned = text.strip()

        # Remove possible markdown fences just in case.
        cleaned = re.sub(r"^```json", "", cleaned)
        cleaned = re.sub(r"^```", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return []

        selected_words = data.get("selected_words", [])

        results = []

        for item in selected_words:
            if not isinstance(item, dict):
                continue

            word_text = item.get("word_text", "")

            if word_text:
                results.append({
                    "word_text": word_text.strip().lower(),
                    "reason": item.get("reason", ""),
                    "context_note": item.get("context_note", "")
                })

        return results

    def select_vocabulary(self, lesson_content, candidate_words, target_level="A1", max_words=8):
        """
        Ask Gemini to select useful vocabulary words.

        If Gemini is unavailable or fails, return an empty list.
        CourseVocabularyService will fallback to rule-based selection.
        """

        if not self.is_available():
            return []

        if not candidate_words:
            return []

        prompt = self.build_prompt(
            lesson_content=lesson_content,
            candidate_words=candidate_words,
            target_level=target_level,
            max_words=max_words
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return self.parse_json_response(response.text)

        except Exception:
            return []