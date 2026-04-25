from flask import Flask
from mongoengine import connect


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Direct connection instead of using the wrapper
    connect(host=app.config['MONGODB_SETTINGS']['host'])
    
    # ... rest of your code
    return app