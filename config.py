import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-please-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

    # Frontend URL
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:3000'

    # Redis (캐시)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'

    # MongoDB (팀/멤버)
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/'
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME') or 'nbc_kakaotalk_bot'

    # PostgreSQL (경기 데이터)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///basketball_games.db'  # 로컬 개발용 SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }