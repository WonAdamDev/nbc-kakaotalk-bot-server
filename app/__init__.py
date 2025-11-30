from flask import Flask
from flask_cors import CORS
from redis import Redis
from pymongo import MongoClient
from config import Config

redis_client = None
mongo_client = None
mongo_db = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    # Redis 초기화
    global redis_client
    try:
        redis_client = Redis.from_url(
            app.config['REDIS_URL'],
            decode_responses=True
        )
        redis_client.ping()
        print(f"[OK] Redis connected: {app.config['REDIS_URL']}")
    except Exception as e:
        print(f"[WARNING] Redis connection failed: {e}")
        redis_client = None

    # MongoDB 초기화 추가
    global mongo_client, mongo_db
    try:
        mongo_client = MongoClient(
            app.config['MONGO_URI'],
            serverSelectionTimeoutMS=5000  # 5초 타임아웃
        )
        # 연결 테스트
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[app.config['MONGO_DB_NAME']]
        print(f"[OK] MongoDB connected: {app.config['MONGO_DB_NAME']}")
    except Exception as e:
        print(f"[WARNING] MongoDB connection failed: {e}")
        mongo_client = None
        mongo_db = None

    from app.routes import commands
    from app.routes.member import commands as member_commands

    app.register_blueprint(commands.bp)
    app.register_blueprint(member_commands.bp)

    from flask import request
    
    @app.route('/health/', methods=['POST'])
    def health_check():
        data = request.get_json()
        print(f"[HEALTH] Received JSON: {data}")

        redis_status = 'ok'
        try:
            if redis_client:
                redis_client.ping()
            else:
                redis_status = 'error'
        except:
            redis_status = 'error'

        mongo_status = 'ok'
        try:
            if mongo_client:
                mongo_client.admin.command('ping')
            else:
                mongo_status = 'error'
        except:
            mongo_status = 'error'

        return {
            'status': 'ok',
            'redis': redis_status,
            'mongodb': mongo_status,
        }, 200

    return app
