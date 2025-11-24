from app import create_app
from config import Config

app = create_app()

if __name__ == '__main__':
    print(f"\n서버 주소: http://{Config.HOST}:{Config.PORT}")
    print(f"Health check: http://localhost:{Config.PORT}/health\n")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
