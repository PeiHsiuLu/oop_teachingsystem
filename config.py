import os

class Config:
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGO_URI', 'mongodb+srv://Three_People:Create_the_Miracle@oop.bzxogsx.mongodb.net/?appName=OOP')
    }