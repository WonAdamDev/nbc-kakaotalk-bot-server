"""
데이터베이스 클리어 스크립트
Usage: python clear_db.py [redis|mongo|all]
"""
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def clear_redis():
    """Redis 클리어"""
    try:
        import redis
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL 환경 변수가 없습니다.")
            return False

        client = redis.from_url(redis_url, decode_responses=True)
        client.flushall()
        print("✅ Redis 클리어 완료")
        return True
    except Exception as e:
        print(f"❌ Redis 클리어 실패: {e}")
        return False

def clear_mongo():
    """MongoDB 클리어"""
    try:
        from pymongo import MongoClient
        from urllib.parse import urlparse

        mongo_url = os.environ.get('MONGO_URI')
        if not mongo_url:
            print("❌ MONGO_URI 환경 변수가 없습니다.")
            return False

        client = MongoClient(mongo_url)

        # URL에서 데이터베이스 이름 추출 또는 기본값 사용
        try:
            db = client.get_default_database()
        except:
            # URL에 DB 이름이 없으면 수동으로 추출하거나 기본값 사용
            parsed_url = urlparse(mongo_url)
            db_name = parsed_url.path.lstrip('/') if parsed_url.path else None

            if not db_name or db_name == '':
                # 모든 데이터베이스 조회
                db_names = client.list_database_names()
                # system DB 제외
                db_names = [name for name in db_names if name not in ['admin', 'local', 'config']]

                if not db_names:
                    print("⚠️  클리어할 데이터베이스가 없습니다.")
                    return True

                # 첫 번째 사용자 DB 사용
                db_name = db_names[0]
                print(f"📂 사용할 데이터베이스: {db_name}")

            db = client[db_name]

        # 모든 collection 삭제
        collection_names = db.list_collection_names()
        deleted_count = 0

        for collection_name in collection_names:
            if not collection_name.startswith('system.'):
                db[collection_name].drop()
                print(f"  - {collection_name} collection 삭제됨")
                deleted_count += 1

        if deleted_count == 0:
            print("⚠️  클리어할 collection이 없습니다.")
        else:
            print(f"✅ MongoDB 클리어 완료 ({deleted_count}개 collection)")

        return True
    except Exception as e:
        print(f"❌ MongoDB 클리어 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'

    print(f"🗑️  데이터베이스 클리어 시작 (target: {target})")
    print("=" * 50)

    if target in ['redis', 'all']:
        clear_redis()

    if target in ['mongo', 'all']:
        clear_mongo()

    print("=" * 50)
    print("✨ 완료")
