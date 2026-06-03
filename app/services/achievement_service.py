from app.models.badge import Badge, AchievementRecord
from app.models.user import Student
from app.models.group_chat import ChatMessage
from app.models.interaction import InteractionSession, InteractionMessage
from app.models.vocabulary_review_log import VocabularyReviewLog
from app.models.vocabulary_practice_log import VocabularyPracticeLog
from app.models.course import ChapterQuizAttempt
from app.models.team_challenge import TeamChallenge


class AchievementService:
    """
    AchievementService manages badge creation, unlock checking,
    and achievement page data.

    This version keeps your original methods:
    - seed_default_badges()
    - unlock_badge()
    - check_level_badge()
    - get_user_achievements()

    So existing routes such as group_chat.py, srs.py, course.py,
    vocabulary_practice.py, and team_challenge.py can still call it safely.
    """

    BADGE_DEFINITIONS = [
        {
            "key": "first_step",
            "name": "First Step｜初次啟程",
            "title_en": "First Step",
            "title_zh": "初次啟程",
            "description": "Create an account and start your learning journey.｜建立帳號並開始你的英文學習旅程。",
            "description_en": "Create an account and start your learning journey.",
            "description_zh": "建立帳號並開始你的英文學習旅程。",
            "icon": "🌱",
            "condition_type": "first_step",
            "required_value": 1,
            "condition_en": "Account created",
            "condition_zh": "已建立帳號",
        },
        {
            "key": "level_2",
            "name": "Level Up｜等級提升",
            "title_en": "Level Up",
            "title_zh": "等級提升",
            "description": "Reach Level 2.｜等級達到 2 級。",
            "description_en": "Reach Level 2.",
            "description_zh": "等級達到 2 級。",
            "icon": "⭐",
            "condition_type": "level_reached",
            "required_value": 2,
            "condition_en": "Level >= 2",
            "condition_zh": "等級達到 2 級",
        },
        {
            "key": "level_5",
            "name": "Rising Learner｜進階學習者",
            "title_en": "Rising Learner",
            "title_zh": "進階學習者",
            "description": "Reach Level 5 and build a steady learning rhythm.｜等級達到 5 級，建立穩定的學習節奏。",
            "description_en": "Reach Level 5 and build a steady learning rhythm.",
            "description_zh": "等級達到 5 級，建立穩定的學習節奏。",
            "icon": "🚀",
            "condition_type": "level_reached",
            "required_value": 5,
            "condition_en": "Level >= 5",
            "condition_zh": "等級達到 5 級",
        },
        {
            "key": "first_message",
            "name": "First Message｜第一次開口",
            "title_en": "First Message",
            "title_zh": "第一次開口",
            "description": "Send your first chat message.｜送出第一則聊天訊息。",
            "description_en": "Send your first chat message.",
            "description_zh": "送出第一則聊天訊息。",
            "icon": "💬",
            "condition_type": "first_message",
            "required_value": 1,
            "condition_en": "Chat messages >= 1",
            "condition_zh": "聊天訊息達到 1 則",
        },
        {
            "key": "chat_10",
            "name": "Conversation Starter｜對話啟動者",
            "title_en": "Conversation Starter",
            "title_zh": "對話啟動者",
            "description": "Send 10 chat messages.｜累積送出 10 則聊天訊息。",
            "description_en": "Send 10 chat messages.",
            "description_zh": "累積送出 10 則聊天訊息。",
            "icon": "🗣️",
            "condition_type": "chat_messages",
            "required_value": 10,
            "condition_en": "Chat messages >= 10",
            "condition_zh": "聊天訊息達到 10 則",
        },
        {
            "key": "word_collector",
            "name": "Word Collector｜單字收藏家",
            "title_en": "Word Collector",
            "title_zh": "單字收藏家",
            "description": "Complete 10 vocabulary reviews.｜完成 10 次單字複習。",
            "description_en": "Complete 10 vocabulary reviews.",
            "description_zh": "完成 10 次單字複習。",
            "icon": "📚",
            "condition_type": "vocabulary_review",
            "required_value": 10,
            "condition_en": "Vocabulary reviews >= 10",
            "condition_zh": "單字複習達到 10 次",
        },
        {
            "key": "sentence_builder",
            "name": "Sentence Builder｜句子建構者",
            "title_en": "Sentence Builder",
            "title_zh": "句子建構者",
            "description": "Complete 20 vocabulary practice exercises.｜完成 20 題單字填空或句子練習。",
            "description_en": "Complete 20 vocabulary practice exercises.",
            "description_zh": "完成 20 題單字填空或句子練習。",
            "icon": "✍️",
            "condition_type": "vocabulary_practice",
            "required_value": 20,
            "condition_en": "Vocabulary practice >= 20",
            "condition_zh": "單字練習達到 20 題",
        },
        {
            "key": "quiz_beginner",
            "name": "Quiz Beginner｜測驗新手",
            "title_en": "Quiz Beginner",
            "title_zh": "測驗新手",
            "description": "Complete your first chapter quiz.｜完成第一次課程測驗。",
            "description_en": "Complete your first chapter quiz.",
            "description_zh": "完成第一次課程測驗。",
            "icon": "🧩",
            "condition_type": "quiz_attempt",
            "required_value": 1,
            "condition_en": "Quiz attempts >= 1",
            "condition_zh": "完成 1 次測驗",
        },
        {
            "key": "perfect_score",
            "name": "Perfect Score｜滿分挑戰者",
            "title_en": "Perfect Score",
            "title_zh": "滿分挑戰者",
            "description": "Get 100 points on any chapter quiz.｜任一課程測驗獲得 100 分。",
            "description_en": "Get 100 points on any chapter quiz.",
            "description_zh": "任一課程測驗獲得 100 分。",
            "icon": "🏆",
            "condition_type": "perfect_score",
            "required_value": 100,
            "condition_en": "Best quiz score = 100",
            "condition_zh": "最高測驗分數達到 100 分",
        },
        {
            "key": "team_challenger",
            "name": "Team Challenger｜團隊挑戰者",
            "title_en": "Team Challenger",
            "title_zh": "團隊挑戰者",
            "description": "Complete and claim a team challenge reward.｜完成並領取一次團隊挑戰獎勵。",
            "description_en": "Complete and claim a team challenge reward.",
            "description_zh": "完成並領取一次團隊挑戰獎勵。",
            "icon": "👥",
            "condition_type": "team_challenge_completed",
            "required_value": 1,
            "condition_en": "Completed team challenges >= 1",
            "condition_zh": "完成團隊挑戰達到 1 次",
        },
    ]

    def _normalize_user(self, user):
        """
        Flask-Login current_user is sometimes a LocalProxy.
        MongoEngine ReferenceField needs the real user document.
        """
        if hasattr(user, "_get_current_object"):
            return user._get_current_object()

        return user

    def seed_default_badges(self):
        """
        Create or update the 10 default badges.

        This does not delete old badges from the database,
        but the achievement page will only display the 10 badges
        defined in BADGE_DEFINITIONS.
        """
        for badge_data in self.BADGE_DEFINITIONS:
            badge = Badge.objects(
                condition_type=badge_data["condition_type"],
                required_value=badge_data["required_value"]
            ).first()

            if not badge:
                badge = Badge.objects(name=badge_data["name"]).first()

            if not badge:
                badge = Badge(
                    name=badge_data["name"],
                    description=badge_data["description"],
                    icon=badge_data["icon"],
                    condition_type=badge_data["condition_type"],
                    required_value=badge_data["required_value"]
                )
            else:
                badge.name = badge_data["name"]
                badge.description = badge_data["description"]
                badge.icon = badge_data["icon"]
                badge.condition_type = badge_data["condition_type"]
                badge.required_value = badge_data["required_value"]

            badge.save()

    def unlock_badge(self, user, condition_type):
        """
        Unlock badge by condition_type.

        Existing routes may call:
        - unlock_badge(user, "first_message")
        - unlock_badge(user, "team_challenge_completed")

        This method still supports those calls.
        """
        user = self._normalize_user(user)
        self.seed_default_badges()

        candidate_badges = Badge.objects(condition_type=condition_type)

        unlocked_records = []

        for badge in candidate_badges:
            existing_record = AchievementRecord.objects(
                user=user,
                badge=badge
            ).first()

            if existing_record:
                unlocked_records.append(existing_record)
                continue

            record = AchievementRecord(
                user=user,
                badge=badge
            )
            record.save()
            unlocked_records.append(record)

        if unlocked_records:
            return unlocked_records[0]

        return None

    def check_level_badge(self, user):
        """
        Unlock level-related badges when user's level reaches the requirement.
        Existing routes already call this method after XP changes.
        """
        user = self._normalize_user(user)
        self.seed_default_badges()

        level = getattr(user, "level", 1) or 1
        latest_record = None

        level_badges = Badge.objects(condition_type="level_reached")

        for badge in level_badges:
            if level >= badge.required_value:
                existing_record = AchievementRecord.objects(
                    user=user,
                    badge=badge
                ).first()

                if existing_record:
                    latest_record = existing_record
                    continue

                latest_record = AchievementRecord(
                    user=user,
                    badge=badge
                )
                latest_record.save()

        return latest_record

    def check_all_badges(self, user):
        """
        Retroactively check all achievements.

        This is useful when the user visits the achievements page:
        old quiz records, review logs, chat records, and level data
        can unlock badges even if the badge did not exist before.
        """
        user = self._normalize_user(user)
        self.seed_default_badges()

        stats = self.get_user_stats(user)

        for badge_data in self.BADGE_DEFINITIONS:
            badge = Badge.objects(
                condition_type=badge_data["condition_type"],
                required_value=badge_data["required_value"]
            ).first()

            if not badge:
                continue

            if self._is_condition_met(badge_data, stats):
                existing_record = AchievementRecord.objects(
                    user=user,
                    badge=badge
                ).first()

                if not existing_record:
                    AchievementRecord(
                        user=user,
                        badge=badge
                    ).save()

    def get_user_achievements(self, user):
        """
        Keep the original API.
        Return unlocked achievement records.
        """
        user = self._normalize_user(user)

        return AchievementRecord.objects(
            user=user
        ).order_by("-unlocked_at")

    def get_achievement_page_data(self, user):
        """
        Return data for the achievements page.
        """
        user = self._normalize_user(user)

        self.check_all_badges(user)

        stats = self.get_user_stats(user)

        achievement_items = []

        for badge_data in self.BADGE_DEFINITIONS:
            badge = Badge.objects(
                condition_type=badge_data["condition_type"],
                required_value=badge_data["required_value"]
            ).first()

            if not badge:
                continue

            record = AchievementRecord.objects(
                user=user,
                badge=badge
            ).first()

            unlocked = record is not None
            progress = self._get_progress_value(badge_data, stats)
            target = badge_data["required_value"]

            if progress > target:
                progress = target

            if target <= 0:
                progress_percent = 0
            else:
                progress_percent = int((progress / target) * 100)

            if progress_percent > 100:
                progress_percent = 100

            achievement_items.append({
                "badge": badge,
                "key": badge_data["key"],
                "icon": badge_data["icon"],
                "title_en": badge_data["title_en"],
                "title_zh": badge_data["title_zh"],
                "description_en": badge_data["description_en"],
                "description_zh": badge_data["description_zh"],
                "condition_en": badge_data["condition_en"],
                "condition_zh": badge_data["condition_zh"],
                "unlocked": unlocked,
                "unlocked_at": record.unlocked_at if record else None,
                "progress": progress,
                "target": target,
                "progress_percent": progress_percent,
            })

        unlocked_count = sum(1 for item in achievement_items if item["unlocked"])
        total_count = len(achievement_items)

        if total_count == 0:
            completion_rate = 0
        else:
            completion_rate = round((unlocked_count / total_count) * 100, 1)

        return {
            "achievements": achievement_items,
            "unlocked_count": unlocked_count,
            "total_count": total_count,
            "completion_rate": completion_rate,
            "stats": stats,
        }

    def get_user_stats(self, user):
        """
        Gather user learning statistics from existing models.
        """
        user = self._normalize_user(user)

        level = getattr(user, "level", 1) or 1
        xp = getattr(user, "xp", 0) or 0

        group_chat_messages = ChatMessage.objects(sender=user).count()

        interaction_sessions = InteractionSession.objects(student=user)
        interaction_messages = InteractionMessage.objects(
            session__in=interaction_sessions,
            role="user"
        ).count()

        chat_messages = group_chat_messages + interaction_messages

        vocabulary_review_count = VocabularyReviewLog.objects(user=user).count()

        stored_review_count = getattr(user, "vocabulary_review_count", 0) or 0
        if stored_review_count > vocabulary_review_count:
            vocabulary_review_count = stored_review_count

        vocabulary_practice_count = VocabularyPracticeLog.objects(user=user).count()

        quiz_attempt_count = ChapterQuizAttempt.objects(student=user).count()

        best_quiz_attempt = ChapterQuizAttempt.objects(
            student=user
        ).order_by("-score").first()

        best_quiz_score = best_quiz_attempt.score if best_quiz_attempt else 0

        completed_team_challenges = self._get_completed_team_challenge_count(user)

        return {
            "level": level,
            "xp": xp,
            "chat_messages": chat_messages,
            "group_chat_messages": group_chat_messages,
            "interaction_messages": interaction_messages,
            "vocabulary_review_count": vocabulary_review_count,
            "vocabulary_practice_count": vocabulary_practice_count,
            "quiz_attempt_count": quiz_attempt_count,
            "best_quiz_score": best_quiz_score,
            "completed_team_challenges": completed_team_challenges,
        }

    def _get_completed_team_challenge_count(self, user):
        """
        Count completed team challenges related to teams the user belongs to.
        """
        try:
            from app.models.team import StudyGroup

            teams = StudyGroup.objects(members=user)

            if not teams:
                return 0

            return TeamChallenge.objects(
                team__in=teams,
                status="completed"
            ).count()

        except Exception:
            return 0

    def _is_condition_met(self, badge_data, stats):
        condition_type = badge_data["condition_type"]
        required_value = badge_data["required_value"]

        if condition_type == "first_step":
            return True

        if condition_type == "level_reached":
            return stats["level"] >= required_value

        if condition_type == "first_message":
            return stats["chat_messages"] >= required_value

        if condition_type == "chat_messages":
            return stats["chat_messages"] >= required_value

        if condition_type == "vocabulary_review":
            return stats["vocabulary_review_count"] >= required_value

        if condition_type == "vocabulary_practice":
            return stats["vocabulary_practice_count"] >= required_value

        if condition_type == "quiz_attempt":
            return stats["quiz_attempt_count"] >= required_value

        if condition_type == "perfect_score":
            return stats["best_quiz_score"] >= required_value

        if condition_type == "team_challenge_completed":
            return stats["completed_team_challenges"] >= required_value

        return False

    def _get_progress_value(self, badge_data, stats):
        condition_type = badge_data["condition_type"]

        if condition_type == "first_step":
            return 1

        if condition_type == "level_reached":
            return stats["level"]

        if condition_type == "first_message":
            return stats["chat_messages"]

        if condition_type == "chat_messages":
            return stats["chat_messages"]

        if condition_type == "vocabulary_review":
            return stats["vocabulary_review_count"]

        if condition_type == "vocabulary_practice":
            return stats["vocabulary_practice_count"]

        if condition_type == "quiz_attempt":
            return stats["quiz_attempt_count"]

        if condition_type == "perfect_score":
            return stats["best_quiz_score"]

        if condition_type == "team_challenge_completed":
            return stats["completed_team_challenges"]

        return 0