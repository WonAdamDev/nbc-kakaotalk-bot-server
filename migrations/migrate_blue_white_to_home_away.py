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

from app import create_app, db
from sqlalchemy import text

def migrate_column_names():
    """컬럼명을 blue/white에서 home/away로 마이그레이션"""
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("Migration: blue/white → home/away (Column Names)")
        print("=" * 70)

        try:
            # games 테이블
            print("\n[1/2] Migrating 'games' table...")

            db.session.execute(text(
                "ALTER TABLE games RENAME COLUMN final_score_blue TO final_score_home"
            ))
            print("  ✓ Renamed: final_score_blue → final_score_home")

            db.session.execute(text(
                "ALTER TABLE games RENAME COLUMN final_score_white TO final_score_away"
            ))
            print("  ✓ Renamed: final_score_white → final_score_away")

            # quarters 테이블
            print("\n[2/2] Migrating 'quarters' table...")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN playing_blue TO playing_home"
            ))
            print("  ✓ Renamed: playing_blue → playing_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN playing_white TO playing_away"
            ))
            print("  ✓ Renamed: playing_white → playing_away")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN bench_blue TO bench_home"
            ))
            print("  ✓ Renamed: bench_blue → bench_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN bench_white TO bench_away"
            ))
            print("  ✓ Renamed: bench_white → bench_away")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN score_blue TO score_home"
            ))
            print("  ✓ Renamed: score_blue → score_home")

            db.session.execute(text(
                "ALTER TABLE quarters RENAME COLUMN score_white TO score_away"
            ))
            print("  ✓ Renamed: score_white → score_away")

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
    print("\n⚠️  WARNING: This migration will rename database columns.")
    print("⚠️  Make sure you have a database backup before proceeding!\n")

    response = input("Continue with migration? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_column_names()
    else:
        print("\nMigration cancelled.")
