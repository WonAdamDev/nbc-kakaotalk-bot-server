"""
Railway 배포용 Seed 스크립트

이 스크립트는 Railway에서 서버 시작 전에 DB를 seed하기 위해 사용됩니다.
Procfile에서 호출됩니다.
"""

import os
import sys

def main():
    from app import create_app, cache_manager
    from app.seed import seed_from_excel

    # Flask 앱 생성 (CacheManager 초기화를 위해)
    app = create_app()

    with app.app_context():
        # 환경 변수에서 파일 경로 읽기
        excel_path = os.environ.get('SEED_FILE_PATH', 'team.xlsx')

        # 파일 존재 확인
        if not os.path.exists(excel_path):
            print(f"[SEED] File not found: {excel_path}")
            print(f"[SEED] Skipping seed process")
            return 0

        # CacheManager 확인
        if not cache_manager:
            print("[SEED ERROR] CacheManager not initialized")
            print("[SEED ERROR] Check Redis and MongoDB connections")
            return 1

        # Seed 실행
        print(f"[SEED] Starting seed with: {excel_path}")
        result = seed_from_excel(cache_manager, excel_path)

        if result['success']:
            print(f"\n[SEED SUCCESS] {result['message']}\n")
            return 0
        else:
            print(f"\n[SEED FAILED] {result['message']}\n")
            # Seed 실패 시에도 서버는 계속 실행되도록 0 반환
            # 실패 시 서버를 중단하려면 return 1 사용
            return 0

if __name__ == '__main__':
    sys.exit(main())
