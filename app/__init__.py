from flask import Flask
from mongoengine import connect
from app.models.user import User, Student, Admin
from app.models.course import LearningPath, Chapter, Unit


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Direct connection instead of using the wrapper
    connect(host=app.config['MONGODB_SETTINGS']['host'])
    
    User.ensure_indexes()
    Student.ensure_indexes()
    Admin.ensure_indexes()

    LearningPath.ensure_indexes()
    Chapter.ensure_indexes()
    Unit.ensure_indexes()


    # ... rest of your code
    return app