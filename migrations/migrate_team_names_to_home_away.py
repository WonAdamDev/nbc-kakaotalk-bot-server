"""
Database Migration: 블루/화이트 → home/away

이 스크립트는 Lineup 테이블의 team 컬럼 값을 변경합니다:
- "블루" → "home"
- "화이트" → "away"
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Lineup
from sqlalchemy import text

def migrate_team_names():
    """팀 이름을 블루/화이트에서 home/away로 마이그레이션"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("Migration: 블루/화이트 → home/away")
        print("=" * 60)

        # 현재 상태 확인
        blue_count = Lineup.query.filter_by(team='블루').count()
        white_count = Lineup.query.filter_by(team='화이트').count()
        home_count = Lineup.query.filter_by(team='home').count()
        away_count = Lineup.query.filter_by(team='away').count()

        print(f"\n[Before Migration]")
        print(f"  블루: {blue_count}")
        print(f"  화이트: {white_count}")
        print(f"  home: {home_count}")
        print(f"  away: {away_count}")

        if blue_count == 0 and white_count == 0:
            print("\n[INFO] No records to migrate (already migrated or empty)")
            return

        # 마이그레이션 실행
        print(f"\n[Migrating...]")

        try:
            # 블루 → home
            blue_records = Lineup.query.filter_by(team='블루').all()
            for record in blue_records:
                record.team = 'home'
            print(f"  Updated {len(blue_records)} records: 블루 → home")

            # 화이트 → away
            white_records = Lineup.query.filter_by(team='화이트').all()
            for record in white_records:
                record.team = 'away'
            print(f"  Updated {len(white_records)} records: 화이트 → away")

            # 커밋
            db.session.commit()
            print(f"\n[SUCCESS] Migration completed!")

            # 마이그레이션 후 상태 확인
            blue_count_after = Lineup.query.filter_by(team='블루').count()
            white_count_after = Lineup.query.filter_by(team='화이트').count()
            home_count_after = Lineup.query.filter_by(team='home').count()
            away_count_after = Lineup.query.filter_by(team='away').count()

            print(f"\n[After Migration]")
            print(f"  블루: {blue_count_after}")
            print(f"  화이트: {white_count_after}")
            print(f"  home: {home_count_after}")
            print(f"  away: {away_count_after}")

        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate_team_names()
