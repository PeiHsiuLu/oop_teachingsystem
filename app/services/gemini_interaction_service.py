import os
import json
import re

from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
except Exception as e:
    print(f"[GeminiInteractionService] google.generativeai import failed: {e}")
    genai = None


class GeminiInteractionService:
    """
    Gemini service for Course Interaction.

    If Gemini fails, it will use fallback reply.
    """

    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip().strip('"').strip("'")

        self.model = None

        print("[GeminiInteractionService] API key loaded:", bool(self.api_key))
        print("[GeminiInteractionService] Model name:", self.model_name)
        print("[GeminiInteractionService] genai imported:", bool(genai))

        if not genai:
            print("[GeminiInteractionService] google-generativeai is not installed or failed to import.")
            return

        if not self.api_key:
            print("[GeminiInteractionService] GEMINI_API_KEY is empty. Using fallback replies.")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print("[GeminiInteractionService] Gemini model initialized successfully.")
        except Exception as e:
            print(f"[GeminiInteractionService] Gemini init failed: {e}")
            self.model = None

    # ============================================================
    # Persona
    # ============================================================

    def get_topic_persona(self, topic):
        title = getattr(topic, "title", "").lower()
        order = getattr(topic, "order", 1)

        if order == 1 or "airport" in title:
            return {
                "role_name": "Airport Check-in Staff",
                "place": "an airport check-in counter",
                "emoji": "✈️",
                "persona": (
                    "You are a friendly airport check-in staff member. "
                    "You help the student check in, confirm tickets, ask about luggage, "
                    "and guide them to the boarding gate."
                ),
            }

        if order == 2 or "hotel" in title:
            return {
                "role_name": "Hotel Front Desk Staff",
                "place": "a hotel front desk",
                "emoji": "🏨",
                "persona": (
                    "You are a polite hotel front desk staff member. "
                    "You help the student check in, ask for booking details, "
                    "explain room facilities, and solve simple hotel problems."
                ),
            }

        if order == 3 or "friend" in title or "people" in title:
            return {
                "role_name": "New Friend",
                "place": "a casual social setting",
                "emoji": "💬",
                "persona": (
                    "You are a friendly person meeting the student for the first time. "
                    "You make small talk, ask about hobbies, daily life, and plans."
                ),
            }

        if order == 4 or "dining" in title or "food" in title:
            return {
                "role_name": "Restaurant Server",
                "place": "a restaurant",
                "emoji": "🍽️",
                "persona": (
                    "You are a helpful restaurant server. "
                    "You help the student order food, explain dishes, ask about preferences, "
                    "and respond to comments about the meal."
                ),
            }

        if order == 5 or "problem" in title or "service" in title:
            return {
                "role_name": "Service Desk Officer",
                "place": "a service desk abroad",
                "emoji": "🧳",
                "persona": (
                    "You are a calm service desk officer. "
                    "You help the student solve travel problems, lost items, complaints, "
                    "and requests for assistance."
                ),
            }

        return {
            "role_name": "AI Tutor",
            "place": "an English practice scenario",
            "emoji": "🤖",
            "persona": (
                "You are a helpful English conversation partner. "
                "You help the student practice realistic spoken English."
            ),
        }

    # ============================================================
    # Prompt
    # ============================================================

    def build_conversation_text(self, messages, max_messages=12):
        recent_messages = list(messages)[-max_messages:]
        lines = []

        for message in recent_messages:
            role = getattr(message, "role", "")
            content = getattr(message, "content", "")

            if role == "user":
                lines.append(f"Student: {content}")
            elif role == "assistant":
                lines.append(f"Partner: {content}")
            else:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def build_reply_prompt(self, topic, student, messages, user_message):
        persona = self.get_topic_persona(topic)
        conversation_text = self.build_conversation_text(messages)
        cefr_level = getattr(student, "cefr_level", "A2")

        return f"""
You are role-playing in an English learning system.

Role: {persona["role_name"]}
Place: {persona["place"]}

Persona:
{persona["persona"]}

Student CEFR level:
{cefr_level}

Rules:
1. Stay in character.
2. Reply only in English.
3. Keep your response suitable for the student's CEFR level.
4. Keep each reply short: 1 to 3 sentences.
5. Ask one natural follow-up question.
6. Do not explain grammar unless the student asks.
7. Do not reveal that you are Gemini or an AI model.
8. Continue the realistic situation.
9. Do not repeat the same sentence unless it is naturally necessary.

Recent conversation:
{conversation_text}

Student just said:
{user_message}

Now reply as {persona["role_name"]}.
"""

    def build_evaluation_prompt(self, topic, student, messages):
        persona = self.get_topic_persona(topic)
        conversation_text = self.build_conversation_text(messages, max_messages=30)
        cefr_level = getattr(student, "cefr_level", "A2")

        return f"""
You are an English learning evaluator.

Topic: {getattr(topic, "title", "")}
Role-play partner: {persona["role_name"]}
Student CEFR level: {cefr_level}

Conversation:
{conversation_text}

Evaluate the student's English performance.

Feedback language rules:
- Each feedback field must be bilingual.
- Use this exact format for each feedback value: English feedback ||| Traditional Chinese feedback
- Do not use slash symbols to separate English and Chinese.
- Keep each field concise and student-friendly.
- Use clear, encouraging wording.
- Do not put bullet marks inside the JSON values. The web page will render bullets.

Return ONLY valid JSON:
{{
  "score": 0,
  "feedback": "English overall feedback. ||| 中文整體回饋。",
  "fluency_feedback": "English fluency feedback. ||| 中文流暢度回饋。",
  "vocabulary_feedback": "English vocabulary feedback. ||| 中文單字用法回饋。",
  "grammar_feedback": "English grammar feedback. ||| 中文文法回饋。",
  "next_suggestion": "English next suggestion. ||| 中文下一步建議。"
}}

Scoring rules:
- Score from 0 to 100.
- Give credit for understandable communication.
- Penalize very short answers, repeated off-topic replies, and serious grammar issues.
- For A2 students, do not be too strict.
"""

    # ============================================================
    # Gemini
    # ============================================================

    def generate_reply(self, topic, student, messages, user_message):
        if not self.model:
            print("[GeminiInteractionService] No Gemini model. Using fallback reply.")
            return self.fallback_reply(topic, user_message)

        prompt = self.build_reply_prompt(
            topic=topic,
            student=student,
            messages=messages,
            user_message=user_message,
        )

        try:
            response = self.model.generate_content(prompt)
            text = getattr(response, "text", "")

            if text and text.strip():
                print("[GeminiInteractionService] Gemini reply generated.")
                return text.strip()

            print("[GeminiInteractionService] Empty Gemini response. Using fallback.")
            return self.fallback_reply(topic, user_message)

        except Exception as e:
            print(f"[GeminiInteractionService] generate_reply failed: {e}")
            return self.fallback_reply(topic, user_message)

    def evaluate_session(self, topic, student, messages):
        if not self.model:
            print("[GeminiInteractionService] No Gemini model. Using fallback evaluation.")
            return self.fallback_evaluation(topic, messages)

        prompt = self.build_evaluation_prompt(
            topic=topic,
            student=student,
            messages=messages,
        )

        try:
            response = self.model.generate_content(prompt)
            text = getattr(response, "text", "").strip()
            data = self.parse_json_from_text(text)

            score = int(data.get("score", 70))
            score = max(0, min(100, score))

            return {
                "score": score,
                "feedback": data.get("feedback", "Good effort. Keep practicing."),
                "fluency_feedback": data.get("fluency_feedback", ""),
                "vocabulary_feedback": data.get("vocabulary_feedback", ""),
                "grammar_feedback": data.get("grammar_feedback", ""),
                "next_suggestion": data.get("next_suggestion", "Try to answer with longer sentences next time."),
            }

        except Exception as e:
            print(f"[GeminiInteractionService] evaluate_session failed: {e}")
            return self.fallback_evaluation(topic, messages)

    def parse_json_from_text(self, text):
        if not text:
            return {}

        cleaned = text.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)

        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return {}

        return {}

    # ============================================================
    # Fallback
    # ============================================================

    def fallback_reply(self, topic, user_message):
        order = getattr(topic, "order", 1)

        if order == 1:
            return "Thank you. May I see your passport and ticket, please?"

        if order == 2:
            return "Welcome to our hotel. May I have your name and booking number?"

        if order == 3:
            return "Nice to meet you. What do you usually like to do in your free time?"

        if order == 4:
            return "Welcome to our restaurant. Would you like to see the menu?"

        if order == 5:
            return "I understand. Could you please tell me what happened?"

        return "Thank you. Can you tell me more?"

    def fallback_evaluation(self, topic, messages):
        user_message_count = 0
        total_words = 0

        for message in messages:
            if getattr(message, "role", "") == "user":
                user_message_count += 1
                total_words += len(getattr(message, "content", "").split())

        score = 60

        if user_message_count >= 3:
            score += 10

        if total_words >= 25:
            score += 10

        if total_words >= 45:
            score += 10

        score = max(0, min(100, score))

        return {
            "score": score,
            "feedback": "Good effort. You completed the conversation practice. ||| 做得不錯，你完成了這次情境對話練習。",
            "fluency_feedback": "Try to answer in complete sentences more often. ||| 可以多嘗試用完整句子回答，讓對話更自然。",
            "vocabulary_feedback": "You used basic vocabulary clearly. ||| 你能清楚使用基本單字來表達意思。",
            "grammar_feedback": "Review sentence structure and verb forms. ||| 建議複習句子結構與動詞形式。",
            "next_suggestion": "Try to give longer answers with more details next time. ||| 下次可以加入更多細節，讓回答更完整。",
        }