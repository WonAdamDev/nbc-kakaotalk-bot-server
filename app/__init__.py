from flask import Flask
from flask_cors import CORS
from redis import Redis
from pymongo import MongoClient
from config import Config
from app.cache_manager import CacheManager
import atexit
import signal
import sys

redis_client = None
mongo_client = None
mongo_db = None
cache_manager = None

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

    # CacheManager 초기화
    global cache_manager
    if redis_client is not None and mongo_db is not None:
        cache_manager = CacheManager(redis_client, mongo_db)
        # 서버 시작 시 MongoDB → Redis 캐시 로드
        print("[CacheManager] Loading data from MongoDB to Redis...")
        cache_manager.load_all_to_cache()

        # Graceful Shutdown 핸들러 등록
        def cleanup_tasks():
            """백그라운드 작업 정리 (atexit용)"""
            print("\n[Shutdown] Graceful shutdown initiated...")
            if cache_manager:
                success = cache_manager.shutdown(timeout=30)
                if success:
                    print("[Shutdown] All tasks completed successfully")
                else:
                    print("[Shutdown] Some tasks were lost due to timeout")
            # atexit에서는 sys.exit() 호출하지 않음

        def signal_handler(signum=None, frame=None):
            """Signal 핸들러 (SIGTERM, SIGINT용)"""
            cleanup_tasks()
            sys.exit(0)

        # atexit: 정상 종료 시 (Ctrl+C, 프로그램 종료)
        atexit.register(cleanup_tasks)

        # signal: SIGTERM, SIGINT 처리 (Railway, Docker 등)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        print("[Shutdown] Graceful shutdown handlers registered")
    else:
        print("[WARNING] CacheManager not initialized (Redis or MongoDB unavailable)")

    from app.routes import commands
    from app.routes.member import commands as member_commands
    from app.routes.team import commands as team_commands
    from app.routes.member_team import commands as member_team_commands

    app.register_blueprint(commands.bp)
    app.register_blueprint(member_commands.bp)
    app.register_blueprint(team_commands.bp)
    app.register_blueprint(member_team_commands.bp)

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
