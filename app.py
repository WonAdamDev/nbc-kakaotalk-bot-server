import argparse
import sys
from app import create_app, cache_manager
from config import Config

def run_seed(excel_path='team.xlsx'):
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
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='NBC KakaoTalk Bot Server')
    parser.add_argument(
        '--seed',
        action='store_true',
        help='team.xlsx 파일로 DB를 seed합니다'
    )
    parser.add_argument(
        '--seed-file',
        type=str,
        default='team.xlsx',
        help='Seed에 사용할 Excel 파일 경로 (기본값: team.xlsx)'
    )

    args = parser.parse_args()

    # Flask 앱 생성
    app = create_app()

    # Seed 모드
    if args.seed:
        success = run_seed(args.seed_file)
        if not success:
            sys.exit(1)  # Seed 실패 시 종료 코드 1
        print("[INFO] Seed 완료. 서버를 계속 실행합니다...\n")

    # 서버 실행
    print(f"\n서버 주소: http://{Config.HOST}:{Config.PORT}")
    print(f"Health check: http://localhost:{Config.PORT}/health\n")

    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
