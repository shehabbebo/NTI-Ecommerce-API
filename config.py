import os
from dotenv import load_dotenv
load_dotenv() 

class Config:
    #SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://united_hanger_user:5122020@localhost/united_hanger_db')
    #SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/mydatabase')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', "sqlite:///mydatabase.db")

    print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'united_hanger_key')

