from flask import Flask
from flask_cors import CORS
from redis import Redis
from config import Config

redis_client = None


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

    from app.routes import commands
    from app.routes.member import commands as member_commands

    app.register_blueprint(commands.bp)
    app.register_blueprint(member_commands.bp)

    @app.route('/health', methods=['POST'])
    def health_check():
        redis_status = 'ok'
        try:
            if redis_client:
                redis_client.ping()
        except:
            redis_status = 'error'

        return {
            'status': 'ok',
            'redis': redis_status
        }, 200

    return app
