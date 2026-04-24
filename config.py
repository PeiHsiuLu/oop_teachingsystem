import os
from dotenv import load_dotenv

# Load variables from a .env file if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///english_system.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False