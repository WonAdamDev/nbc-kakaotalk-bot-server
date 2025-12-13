"""
Database Migration: blue/white → home/away 필드명 변경

이 스크립트는 PostgreSQL 컬럼명을 변경합니다:
- games.final_score_blue → final_score_home
- games.final_score_white → final_score_away
- quarters.playing_blue → playing_home
- quarters.playing_white → playing_away
- quarters.bench_blue → bench_home
- quarters.bench_white → bench_away
- quarters.score_blue → score_home
- quarters.score_white → score_away

실행 방법:
  python migrations/migrate_blue_white_to_home_away.py

Railway에서 실행:
  railway run python migrations/migrate_blue_white_to_home_away.py
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app.models import db
from config import Config
from sqlalchemy import text

def create_minimal_app():
    """마이그레이션용 최소 Flask 앱 생성 (DB만 초기화)"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def migrate_column_names():
    """컬럼명을 blue/white에서 home/away로 마이그레이션"""
    app = create_minimal_app()

    with app.app_context():
        # 데이터베이스 타입 확인
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"\nDatabase URL: {db_url}")

        if 'sqlite' in db_url.lower():
            print("\n[ERROR] This migration is for PostgreSQL only.")
            print("Local SQLite database will use the new schema automatically.")
            print("Please run this migration on Railway production:\n")
            print("  railway run python migrations/migrate_blue_white_to_home_away.py\n")
            return

        if 'postgresql' not in db_url.lower() and 'postgres' not in db_url.lower():
            print("\n[ERROR] Unknown database type. This migration requires PostgreSQL.\n")
            return

        print("=" * 70)
        print("Migration: blue/white -> home/away (Column Names)")
        print("=" * 70)

        try:
            # games 테이블
            print("\n[1/2] Migrating 'games' table...")

            db.session.execute(text(
                "ALTER TABLE games RENAME COLUMN final_score_blue TO final_score_home"
            ))
            print("  [OK] Renamed: final_score_blue -> final_score_home")

            db.session.execute(text(
                "ALTER TABLE games RENAME COLUMN final_score_white TO final_score_away"
            ))
            print("  [OK] Renamed: final_score_white -> final_score_away")

            # quarters 테이블
            print("\n[2/2] Migrating 'quarters' table...")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN playing_blue TO playing_home"
            ))
            print("  [OK] Renamed: playing_blue -> playing_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN playing_white TO playing_away"
            ))
            print("  [OK] Renamed: playing_white -> playing_away")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN bench_blue TO bench_home"
            ))
            print("  [OK] Renamed: bench_blue -> bench_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN bench_white TO bench_away"
            ))
            print("  [OK] Renamed: bench_white -> bench_away")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN score_blue TO score_home"
            ))
            print("  [OK] Renamed: score_blue -> score_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN score_white TO score_away"
            ))
            print("  [OK] Renamed: score_white -> score_away")

            # 커밋
            db.session.commit()

            print("\n" + "=" * 70)
            print("[SUCCESS] All columns renamed successfully!")
            print("=" * 70)
            print("\nNext steps:")
            print("1. Update backend code (models.py, commands.py)")
            print("2. Update frontend code (React components)")
            print("3. Test the application thoroughly")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            print("\nRolling back changes...")
            raise

if __name__ == '__main__':
    print("\n[WARNING] This migration will rename database columns.")
    print("[WARNING] Make sure you have a database backup before proceeding!\n")

    response = input("Continue with migration? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_column_names()
    else:
        print("\nMigration cancelled.")
