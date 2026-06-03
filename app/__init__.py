from dotenv import load_dotenv

load_dotenv()

import os

from flask import Flask
from flask_bcrypt import Bcrypt
from mongoengine import connect
from pymongo.errors import OperationFailure

from app.models.user import User, Student, Admin
from app.models.course import LearningPath, Chapter, Unit
from app.models.word import Word, SentenceGeneratingRule, ReviewItem
from app.models.dialogue import DialogueNode
from app.models.analytics import InteractionLog
from app.models.game import GameEvent
from app.models.badge import Badge as GameBadge
from app.models.report import Report

try:
    from app.models.interaction import (
        InteractionTopic,
        InteractionSession,
        InteractionMessage,
    )
except Exception as e:
    print(f"[Interaction] interaction models not imported: {e}")
    InteractionTopic = None
    InteractionSession = None
    InteractionMessage = None


bcrypt = Bcrypt()


def register_blueprint_once(app, blueprint, *args, **kwargs):
    """
    Register a blueprint only once.

    This prevents:
    ValueError: The name 'interaction' is already registered for this blueprint.
    """

    if blueprint.name in app.blueprints:
        print(f"[Blueprint] Skipped duplicate blueprint: {blueprint.name}")
        return

    app.register_blueprint(blueprint, *args, **kwargs)
    print(f"[Blueprint] Registered blueprint: {blueprint.name}")


def create_app():
    app = Flask(__name__)

    # Load config.py
    app.config.from_object("config.Config")

    # ============================================================
    # Secret Key
    # ============================================================
    # Important:
    # If config.py has SECRET_KEY = None, app.config.get("SECRET_KEY", fallback)
    # will still return None.
    # So we must use "or" fallback.
    # ============================================================

    secret_key = (
        app.config.get("SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or "dev-secret-key-for-local-testing-only"
    )

    app.config["SECRET_KEY"] = secret_key
    app.secret_key = secret_key

    # ============================================================
    # Extensions
    # ============================================================

    bcrypt.init_app(app)

    # ============================================================
    # MongoDB connection
    # ============================================================

    connect(host=app.config["MONGODB_SETTINGS"]["host"])

    # ============================================================
    # Ensure indexes
    # ============================================================

    try:
        User.ensure_indexes()
        Student.ensure_indexes()
        Admin.ensure_indexes()
    except Exception as e:
        print(f"[Index] User indexes skipped: {e}")

    try:
        LearningPath.ensure_indexes()
        Chapter.ensure_indexes()
        Unit.ensure_indexes()
    except Exception as e:
        print(f"[Index] Course indexes skipped: {e}")

    try:
        Word.ensure_indexes()
    except OperationFailure:
        try:
            Word._get_collection().drop_indexes()
            Word.ensure_indexes()
        except Exception as e:
            print(f"[Index] Word index rebuild failed: {e}")
    except Exception as e:
        print(f"[Index] Word indexes skipped: {e}")

    try:
        SentenceGeneratingRule.ensure_indexes()
    except Exception as e:
        print(f"[Index] SentenceGeneratingRule indexes skipped: {e}")

    try:
        ReviewItem.ensure_indexes()
    except Exception as e:
        print(f"[Index] ReviewItem indexes skipped: {e}")

    try:
        DialogueNode.ensure_indexes()
    except Exception as e:
        print(f"[Index] DialogueNode indexes skipped: {e}")

    try:
        InteractionLog.ensure_indexes()
    except Exception as e:
        print(f"[Index] InteractionLog indexes skipped: {e}")

    try:
        GameBadge.ensure_indexes()
        GameEvent.ensure_indexes()
    except Exception as e:
        print(f"[Index] Game indexes skipped: {e}")

    try:
        Report.ensure_indexes()
    except Exception as e:
        print(f"[Index] Report indexes skipped: {e}")

    if InteractionTopic:
        try:
            InteractionTopic.ensure_indexes()
        except Exception as e:
            print(f"[Index] InteractionTopic indexes skipped: {e}")

    if InteractionSession:
        try:
            InteractionSession.ensure_indexes()
        except Exception as e:
            print(f"[Index] InteractionSession indexes skipped: {e}")

    if InteractionMessage:
        try:
            InteractionMessage.ensure_indexes()
        except Exception as e:
            print(f"[Index] InteractionMessage indexes skipped: {e}")

    # ============================================================
    # Register blueprints
    # ============================================================

    from app.routes.auth import auth_bp
    from app.routes.course import course_bp
    from app.routes.word import word_bp
    from app.routes.main import main_bp
    from app.routes.srs import srs_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.team_api import team_bp
    from app.routes.dialogue_api import dialogue_bp
    from app.routes.analytics_api import analytics_bp
    from app.routes.vocabulary_api import vocabulary_bp
    from app.routes.vocabulary_practice import vocabulary_practice_bp
    from app.routes.game_api import game_bp
    from app.routes.report_api import report_bp
    from app.routes.group_chat import group_chat_bp
    from app.routes.achievement import achievement_bp
    from app.routes.team_challenge import team_challenge_bp

    register_blueprint_once(app, achievement_bp)
    register_blueprint_once(app, game_bp)
    register_blueprint_once(app, report_bp)

    register_blueprint_once(app, auth_bp, url_prefix="/auth")
    register_blueprint_once(app, dashboard_bp)
    register_blueprint_once(app, course_bp, url_prefix="/course")
    register_blueprint_once(app, word_bp, url_prefix="/word")
    register_blueprint_once(app, main_bp)
    register_blueprint_once(app, srs_bp, url_prefix="/srs")

    register_blueprint_once(app, team_bp)
    register_blueprint_once(app, dialogue_bp)
    register_blueprint_once(app, analytics_bp)
    register_blueprint_once(app, vocabulary_bp)
    register_blueprint_once(app, vocabulary_practice_bp, url_prefix="/vocabulary")
    register_blueprint_once(app, team_challenge_bp)
    register_blueprint_once(app, group_chat_bp)

    # Course Interaction blueprint
    try:
        from app.routes.interaction import interaction_bp
        register_blueprint_once(app, interaction_bp)
    except Exception as e:
        print(f"[Interaction] interaction_bp not registered: {e}")

    # ============================================================
    # Flask-Login
    # ============================================================

    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()

    # ============================================================
    # Optional services
    # ============================================================

    try:
        from app.services.achievement_service import AchievementService

        achievement_service = AchievementService()
        # achievement_service.seed_default_badges()
    except Exception as e:
        print(f"[Achievement] Service init skipped: {e}")

    return app