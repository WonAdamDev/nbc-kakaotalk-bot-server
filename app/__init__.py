from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from redis import Redis
from pymongo import MongoClient
from config import Config
from app.cache_manager import CacheManager
from app.models import db
import atexit
import signal
import sys

redis_client = None
mongo_client = None
mongo_db = None
cache_manager = None
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS 설정 (프론트엔드 URL 허용)
    # 1. 기본 허용 도메인 (로컬 개발 + 프로덕션)
    cors_origins = [
        "http://localhost:3000",  # 로컬 개발 (Express 서버)
        "http://localhost:5173",  # Vite 개발 서버
    ]

    # 2. 프로덕션 프론트엔드 URL 추가
    frontend_url = app.config.get('FRONTEND_URL')
    if frontend_url:
        # http:// 또는 https:// 없으면 둘 다 추가
        if not frontend_url.startswith('http://') and not frontend_url.startswith('https://'):
            cors_origins.append(f'https://{frontend_url}')
            cors_origins.append(f'http://{frontend_url}')
        else:
            if frontend_url not in cors_origins:
                cors_origins.append(frontend_url)

    print(f"[CORS] Allowed origins: {cors_origins}")

    # 3. CORS 설정
    CORS(app,
         resources={r"/*": {"origins": cors_origins}},
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )

    # PostgreSQL 초기화 (경기 데이터)
    db.init_app(app)

    # WebSocket 초기화 (CORS 설정 포함)
    # REST API와 동일한 도메인만 허용
    # async_mode='gevent': 프로덕션에서 gevent worker 사용 (Python 3.12 호환)
    socketio.init_app(app,
        cors_allowed_origins=cors_origins,
        async_mode='gevent'
    )

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

    # Blueprint 등록
    from app.routes import commands
    from app.routes.member import commands as member_commands
    from app.routes.team import commands as team_commands
    from app.routes.member_team import commands as member_team_commands
    from app.routes.game import commands as game_commands
    from app.routes.admin import commands as admin_commands
    from app.routes import room_routes

    app.register_blueprint(commands.bp)
    app.register_blueprint(member_commands.bp)
    app.register_blueprint(team_commands.bp)
    app.register_blueprint(member_team_commands.bp)
    app.register_blueprint(game_commands.bp)
    app.register_blueprint(admin_commands.bp)
    app.register_blueprint(room_routes.bp)

    # WebSocket 이벤트 핸들러 등록
    from app.routes.game import events

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

        pg_status = 'ok'
        try:
            db.session.execute(db.text('SELECT 1'))
        except:
            pg_status = 'error'

        return {
            'status': 'ok',
            'redis': redis_status,
            'mongodb': mongo_status,
            'postgresql': pg_status,
        }, 200

    # PostgreSQL 테이블 생성 및 마이그레이션
    with app.app_context():
        db.create_all()
        print("[OK] PostgreSQL tables created")

        # lineup_snapshot 컬럼 추가 (마이그레이션)
        try:
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)

            # quarters 테이블에 lineup_snapshot 컬럼이 있는지 확인
            columns = [col['name'] for col in inspector.get_columns('quarters')]

            if 'lineup_snapshot' not in columns:
                print("[Migration] Adding lineup_snapshot column to quarters table...")
                db.session.execute(text(
                    "ALTER TABLE quarters ADD COLUMN lineup_snapshot JSON"
                ))
                db.session.commit()
                print("[OK] lineup_snapshot column added")
            else:
                print("[OK] lineup_snapshot column already exists")
        except Exception as e:
            print(f"[WARNING] Migration check failed: {e}")
            db.session.rollback()

    return app
