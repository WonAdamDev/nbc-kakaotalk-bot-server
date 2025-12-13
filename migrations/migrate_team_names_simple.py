"""
Database Migration: 블루/화이트 → home/away (Simple Version)

이 스크립트는 Lineup 테이블의 team 컬럼 값을 변경합니다:
- "블루" → "home"
- "화이트" → "away"

SocketIO 없이 직접 데이터베이스에 연결합니다.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def migrate_team_names():
    """팀 이름을 블루/화이트에서 home/away로 마이그레이션"""

    # 환경변수에서 DATABASE_URL 가져오기
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_URL environment variable not found")
        return

    # PostgreSQL URL 수정 (Railway에서 postgres://로 시작하면 postgresql://로 변경)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print("=" * 60)
    print("Migration: 블루/화이트 → home/away")
    print("=" * 60)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'hidden'}")

    # 데이터베이스 연결
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 테이블 존재 확인
        print(f"\n[Checking tables...]")
        table_exists = session.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'lineups')"
        )).scalar()

        if not table_exists:
            print("[ERROR] Table 'lineups' does not exist")
            session.close()
            return

        print(f"  Table 'lineups' found ✓")

        # 현재 상태 확인
        print(f"\n[Before Migration]")
        blue_count = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = '블루'")).scalar()
        white_count = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = '화이트'")).scalar()
        home_count = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = 'home'")).scalar()
        away_count = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = 'away'")).scalar()

        print(f"  블루: {blue_count}")
        print(f"  화이트: {white_count}")
        print(f"  home: {home_count}")
        print(f"  away: {away_count}")

        if blue_count == 0 and white_count == 0:
            print("\n[INFO] No records to migrate (already migrated or empty)")
            session.close()
            return

        # 마이그레이션 실행
        print(f"\n[Migrating...]")

        # 블루 → home
        result_blue = session.execute(
            text("UPDATE lineups SET team = 'home' WHERE team = '블루'")
        )
        print(f"  Updated {result_blue.rowcount} records: 블루 → home")

        # 화이트 → away
        result_white = session.execute(
            text("UPDATE lineups SET team = 'away' WHERE team = '화이트'")
        )
        print(f"  Updated {result_white.rowcount} records: 화이트 → away")

        # 커밋
        session.commit()
        print(f"\n[SUCCESS] Migration completed!")

        # 마이그레이션 후 상태 확인
        print(f"\n[After Migration]")
        blue_count_after = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = '블루'")).scalar()
        white_count_after = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = '화이트'")).scalar()
        home_count_after = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = 'home'")).scalar()
        away_count_after = session.execute(text("SELECT COUNT(*) FROM lineups WHERE team = 'away'")).scalar()

        print(f"  블루: {blue_count_after}")
        print(f"  화이트: {white_count_after}")
        print(f"  home: {home_count_after}")
        print(f"  away: {away_count_after}")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Migration failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"\nFull traceback:")
        traceback.print_exc()
        raise
    finally:
        session.close()
        engine.dispose()

if __name__ == '__main__':
    migrate_team_names()
