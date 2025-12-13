"""
MongoDB 팀/멤버 ID 마이그레이션 스크립트
- 기존 key-value 구조를 document 구조로 변환
- team_id, member_id 발급
"""
import uuid
from pymongo import MongoClient
from redis import Redis
import os


def generate_id(prefix):
    """8자리 UUID 생성"""
    return f"{prefix}_{str(uuid.uuid4())[:8].upper()}"


def migrate_teams_and_members(mongo_uri, mongo_db_name, redis_url):
    """팀과 멤버 데이터 마이그레이션"""

    # MongoDB 연결
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[mongo_db_name]

    # Redis 연결
    redis_client = Redis.from_url(redis_url, decode_responses=True)

    print("[Migration] Starting MongoDB/Redis migration...")

    # 1. 기존 teams 컬렉션을 teams_new로 마이그레이션
    teams_collection = db['teams']
    members_collection = db['members']

    # 기존 데이터 백업
    print("[Migration] Backing up existing data...")
    db['teams_backup'] = db['teams']
    db['members_backup'] = db['members']

    # 2. Redis에서 팀 데이터 읽기
    team_keys = redis_client.keys('room:*:team:*')
    room_teams = {}  # {room_id: {team_name: team_id}}

    print(f"[Migration] Found {len(team_keys)} teams in Redis")

    for key in team_keys:
        # key 형식: room:{room}:team:{team_name}
        parts = key.split(':')
        if len(parts) >= 4:
            room_name = parts[1]
            team_name = ':'.join(parts[3:])  # 팀 이름에 ':' 있을 수 있음

            # room_id 가져오기 (rooms 테이블에서)
            # 여기서는 임시로 room_name을 해시하여 생성
            room_id = str(uuid.uuid4())[:8].upper()

            # team_id 생성
            team_id = generate_id('TEAM')

            if room_name not in room_teams:
                room_teams[room_name] = {}
            room_teams[room_name][team_name] = team_id

            # MongoDB에 저장
            teams_collection.update_one(
                {'room_name': room_name, 'name': team_name},
                {
                    '$set': {
                        '_id': team_id,
                        'room_id': room_id,  # 나중에 rooms 테이블과 연동 필요
                        'room_name': room_name,  # 임시
                        'name': team_name,
                        'migrated': True
                    }
                },
                upsert=True
            )

            print(f"  - Migrated team: {room_name}/{team_name} → {team_id}")

    # 3. Redis에서 멤버 데이터 읽기
    member_keys = redis_client.keys('room:*:member:*')
    print(f"\n[Migration] Found {len(member_keys)} members in Redis")

    for key in member_keys:
        # key 형식: room:{room}:member:{member_name}
        parts = key.split(':')
        if len(parts) >= 4:
            room_name = parts[1]
            member_name = ':'.join(parts[3:])

            # 멤버의 팀 찾기
            team_key = f"room:{room_name}:member_team:{member_name}"
            team_name = redis_client.get(team_key)

            # member_id 생성
            member_id = generate_id('MEM')

            # team_id 찾기
            team_id = None
            if team_name and room_name in room_teams and team_name in room_teams[room_name]:
                team_id = room_teams[room_name][team_name]

            # MongoDB에 저장
            members_collection.update_one(
                {'room_name': room_name, 'name': member_name},
                {
                    '$set': {
                        '_id': member_id,
                        'room_id': None,  # 나중에 업데이트 필요
                        'room_name': room_name,  # 임시
                        'name': member_name,
                        'team_id': team_id,
                        'team_name': team_name,  # 임시
                        'migrated': True
                    }
                },
                upsert=True
            )

            print(f"  - Migrated member: {room_name}/{member_name} → {member_id} (team: {team_name})")

    print("\n[Migration] Migration completed!")
    print(f"  - Teams migrated: {len(team_keys)}")
    print(f"  - Members migrated: {len(member_keys)}")
    print("\n[Note] room_id fields need to be updated after rooms table is populated")

    return {
        'teams': len(team_keys),
        'members': len(member_keys)
    }


if __name__ == '__main__':
    # 환경 변수에서 설정 읽기
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nbc_basketball')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

    print("=" * 60)
    print("MongoDB/Redis Migration Script")
    print("=" * 60)
    print(f"MongoDB: {MONGO_URI}")
    print(f"Database: {MONGO_DB_NAME}")
    print(f"Redis: {REDIS_URL}")
    print("=" * 60)

    confirm = input("\nProceed with migration? (yes/no): ")
    if confirm.lower() == 'yes':
        result = migrate_teams_and_members(MONGO_URI, MONGO_DB_NAME, REDIS_URL)
        print("\n✅ Migration successful!")
    else:
        print("\n❌ Migration cancelled")
