from flask import Flask
from flask_bcrypt import Bcrypt
from mongoengine import connect
from app.models.user import User, Student, Admin
from app.models.course import LearningPath, Chapter, Unit
from app.models.word import Word, SentenceGeneratingRule, ReviewItem
from app.models.dialogue import DialogueNode
from app.models.analytics import InteractionLog
from app.models.game import Badge, GameEvent
from app.models.report import Report

bcrypt = Bcrypt()

def create_app():
    # The template_folder is set to 'routes' because the HTML files are currently in that directory.
    # The standard practice is to have a 'templates' folder.
    # app = Flask(__name__, template_folder='routes')
    app = Flask(__name__)
    app.config.from_object('config.Config')
    # A secret key is required for session management (e.g., for flash messages).
    app.config['SECRET_KEY'] = 'a-very-hard-to-guess-string' # Change this for production!

    bcrypt.init_app(app)
    
    # Direct connection instead of using the wrapper
    connect(host=app.config['MONGODB_SETTINGS']['host'])
    
    User.ensure_indexes()
    Student.ensure_indexes()
    Admin.ensure_indexes()
    
    # Course models
    LearningPath.ensure_indexes()
    Chapter.ensure_indexes()
    Unit.ensure_indexes()
    
    # New: Word database models
    Word.ensure_indexes()
    SentenceGeneratingRule.ensure_indexes()
    ReviewItem.ensure_indexes()

    # New: Dialogue and Analytics models
    DialogueNode.ensure_indexes()
    InteractionLog.ensure_indexes()

    Badge.ensure_indexes()
    GameEvent.ensure_indexes()
    Report.ensure_indexes()

    # Register blueprints (assuming these exist in the full __init__.py)
    from app.routes.auth import auth_bp
    from app.routes.course import course_bp
    from app.routes.word import word_bp
    from app.routes.main import main_bp
    from app.routes.srs import srs_bp # New: SRS routes
    from app.routes.dashboard import dashboard_bp
    from app.routes.team_api import team_bp
    from app.routes.dialogue_api import dialogue_bp
    from app.routes.analytics_api import analytics_bp
    from app.routes.vocabulary_api import vocabulary_bp
    from app.routes.game_api import game_bp
    from app.routes.report_api import report_bp

    app.register_blueprint(game_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(course_bp, url_prefix='/course')
    app.register_blueprint(word_bp, url_prefix='/word')
    app.register_blueprint(main_bp) # Register at root
    app.register_blueprint(srs_bp, url_prefix='/srs') # New: SRS routes
    app.register_blueprint(team_bp)
    app.register_blueprint(dialogue_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(vocabulary_bp)

    # Initialize Flask-Login (assuming this exists in the full __init__.py)
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Redirect to auth.login if not logged in

    @login_manager.user_loader
    def load_user(user_id):
        # user_id is the string representation of the ObjectId
        return User.objects(id=user_id).first()

    return app