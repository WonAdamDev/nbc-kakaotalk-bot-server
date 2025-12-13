"""
팀/멤버 ID 마이그레이션 스크립트 (개선 버전)

기존 Redis/MongoDB 팀/멤버 데이터를 새로운 document 구조로 변환:
- team_id, member_id 발급
- room_name 기반 구조로 변경
"""
import uuid
import os
import sys
from pymongo import MongoClient


def generate_id(prefix):
    """8자리 UUID 생성"""
    return f"{prefix}_{str(uuid.uuid4())[:8].upper()}"


def migrate_teams_and_members():
    """
    팀과 멤버 데이터를 새 구조로 마이그레이션

    기존 구조 (Redis key-value):
        teams 컬렉션: {"_id": "room:방이름:team:팀이름", "value": "팀이름"}
        members 컬렉션: {"_id": "room:방이름:member:멤버이름", "value": "멤버이름"}
        member_teams 컬렉션: {"_id": "room:방이름:member:멤버이름", "value": "팀이름"}

    새 구조 (Document):
        teams: {"_id": "TEAM_X7Y2K9P3", "room_name": "방이름", "name": "팀이름", "created_at": ...}
        members: {"_id": "MEM_X7Y2K9P3", "room_name": "방이름", "name": "멤버이름", "team_id": "TEAM_xxx", "created_at": ...}
    """

    # 환경 변수에서 설정 읽기
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nbc_basketball')

    # MongoDB 연결
    print(f"[Migration] Connecting to MongoDB: {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    teams_col = db['teams']
    members_col = db['members']
    member_teams_col = db['member_teams']

    print("\n" + "=" * 60)
    print("팀/멤버 ID 마이그레이션 시작")
    print("=" * 60)

    # 1. 기존 teams 컬렉션에서 key-value 구조 찾기
    print("\n[1/4] 기존 팀 데이터 조회 중...")
    old_teams = list(teams_col.find({"value": {"$exists": True}}))
    print(f"  → 발견: {len(old_teams)}개 팀 (key-value 구조)")

    # 2. 팀 마이그레이션 및 매핑 테이블 생성
    print("\n[2/4] 팀 데이터 마이그레이션 중...")
    team_name_to_id = {}  # {(room_name, team_name): team_id}
    migrated_teams = 0
    skipped_teams = 0

    for team_doc in old_teams:
        key = team_doc.get('_id')  # "room:방이름:team:팀이름"
        team_name = team_doc.get('value')

        # 키 파싱
        if not key or not key.startswith('room:') or ':team:' not in key:
            print(f"  ⚠️ 잘못된 키 형식: {key}")
            continue

        parts = key.split(':team:')
        room_name = parts[0].replace('room:', '')

        # 중복 확인
        existing = teams_col.find_one({
            'room_name': room_name,
            'name': team_name,
            '_id': {'$not': {'$regex': '^room:'}}  # 새 구조만
        })

        if existing:
            team_id = existing['_id']
            skipped_teams += 1
            print(f"  ⏭️  이미 존재: {room_name}/{team_name} → {team_id}")
        else:
            # 새 팀 ID 발급 및 저장
            team_id = generate_id('TEAM')
            new_team = {
                '_id': team_id,
                'room_name': room_name,
                'name': team_name
            }
            teams_col.insert_one(new_team)
            migrated_teams += 1
            print(f"  ✅ {room_name}/{team_name} → {team_id}")

        # 매핑 테이블에 추가
        team_name_to_id[(room_name, team_name)] = team_id

    print(f"\n  완료: {migrated_teams}개 생성, {skipped_teams}개 건너뜀")

    # 3. 기존 members 컬렉션에서 key-value 구조 찾기
    print("\n[3/4] 기존 멤버 데이터 조회 중...")
    old_members = list(members_col.find({"value": {"$exists": True}}))
    print(f"  → 발견: {len(old_members)}개 멤버 (key-value 구조)")

    # 4. 멤버 마이그레이션
    print("\n[4/4] 멤버 데이터 마이그레이션 중...")
    migrated_members = 0
    skipped_members = 0

    for member_doc in old_members:
        key = member_doc.get('_id')  # "room:방이름:member:멤버이름"
        member_name = member_doc.get('value')

        # 키 파싱
        if not key or not key.startswith('room:') or ':member:' not in key:
            print(f"  ⚠️ 잘못된 키 형식: {key}")
            continue

        parts = key.split(':member:')
        room_name = parts[0].replace('room:', '')

        # 중복 확인
        existing = members_col.find_one({
            'room_name': room_name,
            'name': member_name,
            '_id': {'$not': {'$regex': '^room:'}}  # 새 구조만
        })

        if existing:
            skipped_members += 1
            print(f"  ⏭️  이미 존재: {room_name}/{member_name} → {existing['_id']}")
            continue

        # 팀 배정 확인 (member_teams 컬렉션에서)
        team_assignment = member_teams_col.find_one({'_id': key})
        team_name = team_assignment.get('value') if team_assignment else None
        team_id = None

        if team_name:
            team_id = team_name_to_id.get((room_name, team_name))
            if not team_id:
                print(f"  ⚠️ 팀을 찾을 수 없음: {room_name}/{team_name}")

        # 새 멤버 ID 발급 및 저장
        member_id = generate_id('MEM')
        new_member = {
            '_id': member_id,
            'room_name': room_name,
            'name': member_name,
            'team_id': team_id
        }
        members_col.insert_one(new_member)
        migrated_members += 1

        team_info = f" (팀: {team_name} / {team_id})" if team_id else " (팀 없음)"
        print(f"  ✅ {room_name}/{member_name} → {member_id}{team_info}")

    print(f"\n  완료: {migrated_members}개 생성, {skipped_members}개 건너뜀")

    # 5. 요약
    print("\n" + "=" * 60)
    print("마이그레이션 완료!")
    print("=" * 60)
    print(f"팀: {migrated_teams}개 생성, {skipped_teams}개 건너뜀")
    print(f"멤버: {migrated_members}개 생성, {skipped_members}개 건너뜀")
    print("\n⚠️  중요: PostgreSQL 마이그레이션도 실행하세요!")
    print("   psql -U your_user -d your_database -f migrations/add_member_ids_to_lineups.sql")
    print("=" * 60)


if __name__ == '__main__':
    print("=" * 60)
    print("팀/멤버 ID 마이그레이션 스크립트")
    print("=" * 60)
    print("\n⚠️  주의사항:")
    print("  - 이 스크립트는 MongoDB의 teams/members 컬렉션을 수정합니다")
    print("  - 기존 key-value 구조를 새 document 구조로 변환합니다")
    print("  - 중복 데이터는 건너뜁니다 (안전)")
    print("  - 원본 데이터는 유지됩니다")
    print("\n환경 변수:")
    print(f"  MONGO_URI: {os.getenv('MONGO_URI', 'mongodb://localhost:27017/')}")
    print(f"  MONGO_DB_NAME: {os.getenv('MONGO_DB_NAME', 'nbc_basketball')}")

    confirm = input("\n계속하시겠습니까? (yes/no): ")
    if confirm.lower() == 'yes':
        migrate_teams_and_members()
    else:
        print("\n❌ 마이그레이션 취소")
        sys.exit(0)
