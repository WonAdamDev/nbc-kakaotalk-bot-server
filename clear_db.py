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
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            print("❌ MONGO_URL 환경 변수가 없습니다.")
            return False

        client = MongoClient(mongo_url)
        db = client.get_default_database()

        # 모든 collection 삭제
        collection_names = db.list_collection_names()
        for collection_name in collection_names:
            if not collection_name.startswith('system.'):
                db[collection_name].drop()
                print(f"  - {collection_name} collection 삭제됨")

        print("✅ MongoDB 클리어 완료")
        return True
    except Exception as e:
        print(f"❌ MongoDB 클리어 실패: {e}")
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
