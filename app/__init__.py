from flask import Flask
from flask_cors import CORS
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    from app.routes import commands
    app.register_blueprint(commands.bp)

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}, 200

    return app
