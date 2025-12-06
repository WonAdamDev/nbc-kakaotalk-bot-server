import sys
from app import create_app, cache_manager
from config import Config

def run_seed(excel_path):
    """Seed 실행 함수"""
    from app.seed import seed_from_excel

    if not cache_manager:
        print("[ERROR] CacheManager가 초기화되지 않았습니다.")
        print("Redis와 MongoDB가 모두 실행 중인지 확인하세요.")
        return False

    print(f"\n[SEED] Starting seed process with file: {excel_path}")
    result = seed_from_excel(cache_manager, excel_path)

    if result['success']:
        print(f"\n[SEED SUCCESS] {result['message']}\n")
        return True
    else:
        print(f"\n[SEED FAILED] {result['message']}\n")
        return False

if __name__ == '__main__':
    # Flask 앱 생성
    app = create_app()

    # 환경 변수로 Seed 여부 확인
    if Config.ENABLE_SEED:
        print(f"[INFO] ENABLE_SEED=True, starting seed process...")
        success = run_seed(Config.SEED_FILE_PATH)
        if not success:
            print("[WARNING] Seed failed, but server will continue...")
        else:
            print("[INFO] Seed 완료. 서버를 계속 실행합니다...\n")
    else:
        print(f"[INFO] ENABLE_SEED=False, skipping seed process")

    # 서버 실행
    print(f"\n서버 주소: http://{Config.HOST}:{Config.PORT}")
    print(f"Health check: http://localhost:{Config.PORT}/health\n")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
