"""
Cache Manager - Redis + MongoDB Write-Behind Pattern

Redis에 먼저 쓰고 즉시 응답한 후, 백그라운드에서 MongoDB에 저장하는 패턴을 구현합니다.
"""

import json
import threading
import queue
import time
from typing import Any, Optional, Dict
from datetime import datetime
from enum import Enum


class TaskType(Enum):
    """MongoDB 작업 타입"""
    SET = "set"
    DELETE = "delete"
    INCREMENT = "increment"


class DBTask:
    """MongoDB에 수행할 작업을 나타내는 클래스"""
    def __init__(self, task_type: TaskType, collection: str, key: str,
                 value: Any = None, field: str = None, amount: int = 1):
        self.task_type = task_type
        self.collection = collection
        self.key = key
        self.value = value
        self.field = field
        self.amount = amount
        self.timestamp = datetime.now()


class TaskQueue:
    """백그라운드 작업 큐 (싱글톤)"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.task_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.mongo_db = None
        self._initialized = True

    def start(self, mongo_db):
        """워커 스레드 시작"""
        if self.running:
            return

        self.mongo_db = mongo_db
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        print("[TaskQueue] Background worker started")

    def stop(self, timeout=30):
        """
        워커 스레드 종료 (Graceful Shutdown)

        Args:
            timeout: 최대 대기 시간 (초), 기본 30초
        """
        if not self.running:
            print("[TaskQueue] Already stopped")
            return

        queue_size = self.task_queue.qsize()
        if queue_size > 0:
            print(f"[TaskQueue] Graceful shutdown started. Processing {queue_size} remaining tasks...")

        # 큐의 모든 작업이 완료될 때까지 대기
        start_time = time.time()
        while not self.task_queue.empty():
            elapsed = time.time() - start_time
            if elapsed > timeout:
                remaining = self.task_queue.qsize()
                print(f"[TaskQueue] Shutdown timeout after {timeout}s. {remaining} tasks remaining (will be lost)")
                break

            # 0.1초마다 큐 확인
            time.sleep(0.1)

        # 워커 종료
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        final_size = self.task_queue.qsize()
        if final_size == 0:
            print("[TaskQueue] Graceful shutdown completed. All tasks processed.")
        else:
            print(f"[TaskQueue] Shutdown completed with {final_size} tasks lost.")

        return final_size == 0

    def add_task(self, task: DBTask):
        """작업을 큐에 추가"""
        self.task_queue.put(task)

    def _worker(self):
        """백그라운드 워커 - 큐에서 작업을 꺼내 MongoDB에 저장"""
        while self.running:
            try:
                # 타임아웃을 두고 작업 가져오기 (종료 시그널 확인용)
                task = self.task_queue.get(timeout=1)

                if self.mongo_db is None:
                    print(f"[TaskQueue] MongoDB not connected, skipping task")
                    continue

                # MongoDB 작업 수행
                try:
                    collection = self.mongo_db[task.collection]

                    if task.task_type == TaskType.SET:
                        # Upsert: key로 찾아서 있으면 업데이트, 없으면 삽입
                        collection.update_one(
                            {"_id": task.key},
                            {"$set": {
                                "value": task.value,
                                "updated_at": task.timestamp
                            }},
                            upsert=True
                        )
                        print(f"[TaskQueue] SET {task.collection}:{task.key}")

                    elif task.task_type == TaskType.DELETE:
                        collection.delete_one({"_id": task.key})
                        print(f"[TaskQueue] DELETE {task.collection}:{task.key}")

                    elif task.task_type == TaskType.INCREMENT:
                        # 증가 작업
                        collection.update_one(
                            {"_id": task.key},
                            {
                                "$inc": {f"value.{task.field}": task.amount},
                                "$set": {"updated_at": task.timestamp}
                            },
                            upsert=True
                        )
                        print(f"[TaskQueue] INCREMENT {task.collection}:{task.key}.{task.field} by {task.amount}")

                except Exception as e:
                    print(f"[TaskQueue] Error processing task: {e}")

                finally:
                    self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TaskQueue] Worker error: {e}")


class CacheManager:
    """
    Redis + MongoDB Cache Manager

    Redis를 1차 캐시로 사용하고, MongoDB를 영구 저장소로 사용합니다.
    Write-Behind 패턴: Redis에 먼저 쓰고 즉시 응답 → 백그라운드에서 MongoDB에 저장
    """

    def __init__(self, redis_client, mongo_db):
        self.redis = redis_client
        self.mongo_db = mongo_db
        self.task_queue = TaskQueue()

        # 백그라운드 워커 시작
        if mongo_db is not None:
            self.task_queue.start(mongo_db)

    def shutdown(self, timeout=30):
        """
        Graceful shutdown - 모든 대기 중인 작업 완료 후 종료

        Args:
            timeout: 최대 대기 시간 (초)

        Returns:
            모든 작업이 완료되었으면 True, 타임아웃으로 일부 손실되면 False
        """
        return self.task_queue.stop(timeout=timeout)

    def _redis_key(self, collection: str, key: str) -> str:
        """Redis 키 생성: collection:key"""
        return f"{collection}:{key}"

    def get(self, collection: str, key: str, default: Any = None) -> Any:
        """
        데이터 조회 (Redis → MongoDB 순서)

        Args:
            collection: 컬렉션 이름
            key: 키
            default: 기본값 (없을 때 반환)

        Returns:
            조회된 값 또는 기본값
        """
        redis_key = self._redis_key(collection, key)

        # 1. Redis에서 먼저 조회
        if self.redis:
            try:
                cached = self.redis.get(redis_key)
                if cached is not None:
                    print(f"[CacheManager] Redis GET hit: {redis_key} = {cached}")
                    try:
                        return json.loads(cached)
                    except json.JSONDecodeError:
                        return cached
                else:
                    print(f"[CacheManager] Redis GET miss: {redis_key}")
            except Exception as e:
                print(f"[CacheManager] Redis GET error: {e}")

        # 2. Redis에 없으면 MongoDB에서 조회
        if self.mongo_db is not None:
            try:
                doc = self.mongo_db[collection].find_one({"_id": key})
                if doc and "value" in doc:
                    value = doc["value"]
                    print(f"[CacheManager] MongoDB GET hit: {collection}.{key} = {value}")
                    # Redis에 캐시
                    if self.redis:
                        try:
                            self.redis.setex(
                                redis_key,
                                3600,  # 1시간 TTL
                                json.dumps(value) if isinstance(value, (dict, list)) else value
                            )
                            print(f"[CacheManager] Cached to Redis: {redis_key}")
                        except Exception as e:
                            print(f"[CacheManager] Redis cache error: {e}")
                    return value
                else:
                    print(f"[CacheManager] MongoDB GET miss: {collection}.{key}")
            except Exception as e:
                print(f"[CacheManager] MongoDB GET error: {e}")

        print(f"[CacheManager] GET returned default for {redis_key}")
        return default

    def set(self, collection: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        데이터 저장 (Write-Behind)

        1. Redis에 즉시 저장
        2. 백그라운드에서 MongoDB에 저장

        Args:
            collection: 컬렉션 이름
            key: 키
            value: 저장할 값
            ttl: Redis TTL (초 단위, None이면 기본 1시간)

        Returns:
            성공 여부
        """
        redis_key = self._redis_key(collection, key)
        ttl = ttl or 3600  # 기본 1시간

        # 1. Redis에 즉시 저장
        if self.redis:
            try:
                serialized = json.dumps(value) if isinstance(value, (dict, list)) else value
                self.redis.setex(redis_key, ttl, serialized)
                print(f"[CacheManager] Redis SET success: {redis_key} = {value} (TTL: {ttl}s)")
            except Exception as e:
                print(f"[CacheManager] Redis SET error: {e}")
                return False
        else:
            print(f"[CacheManager] Redis not available, skipping SET for {redis_key}")

        # 2. MongoDB 저장 작업을 백그라운드 큐에 추가
        if self.mongo_db is not None:
            task = DBTask(TaskType.SET, collection, key, value)
            self.task_queue.add_task(task)

        return True

    def delete(self, collection: str, key: str) -> bool:
        """
        데이터 삭제 (Redis + MongoDB)

        Args:
            collection: 컬렉션 이름
            key: 키

        Returns:
            성공 여부
        """
        redis_key = self._redis_key(collection, key)

        # 1. Redis에서 즉시 삭제
        if self.redis:
            try:
                self.redis.delete(redis_key)
            except Exception as e:
                print(f"[CacheManager] Redis DELETE error: {e}")

        # 2. MongoDB 삭제 작업을 백그라운드 큐에 추가
        if self.mongo_db is not None:
            task = DBTask(TaskType.DELETE, collection, key)
            self.task_queue.add_task(task)

        return True

    def increment(self, collection: str, key: str, field: str = "count", amount: int = 1) -> int:
        """
        카운터 증가 (Write-Behind)

        Args:
            collection: 컬렉션 이름
            key: 키
            field: 증가시킬 필드명
            amount: 증가량

        Returns:
            증가 후 값
        """
        redis_key = self._redis_key(collection, key)
        redis_hash_key = f"{redis_key}:hash"

        # 1. Redis에서 즉시 증가
        new_value = amount
        if self.redis:
            try:
                new_value = self.redis.hincrby(redis_hash_key, field, amount)
                # TTL 설정
                self.redis.expire(redis_hash_key, 3600)
            except Exception as e:
                print(f"[CacheManager] Redis INCREMENT error: {e}")

        # 2. MongoDB 증가 작업을 백그라운드 큐에 추가
        if self.mongo_db is not None:
            task = DBTask(TaskType.INCREMENT, collection, key, field=field, amount=amount)
            self.task_queue.add_task(task)

        return new_value

    def get_hash(self, collection: str, key: str) -> Dict:
        """
        해시 전체 조회

        Args:
            collection: 컬렉션 이름
            key: 키

        Returns:
            해시 딕셔너리
        """
        redis_key = self._redis_key(collection, key)
        redis_hash_key = f"{redis_key}:hash"

        # Redis에서 조회
        if self.redis:
            try:
                hash_data = self.redis.hgetall(redis_hash_key)
                if hash_data:
                    # 문자열 값을 정수로 변환 (카운터 등)
                    return {k: int(v) if v.isdigit() else v for k, v in hash_data.items()}
            except Exception as e:
                print(f"[CacheManager] Redis HGETALL error: {e}")

        # MongoDB에서 조회
        if self.mongo_db is not None:
            try:
                doc = self.mongo_db[collection].find_one({"_id": key})
                if doc and "value" in doc:
                    return doc["value"]
            except Exception as e:
                print(f"[CacheManager] MongoDB HGETALL error: {e}")

        return {}

    def find_keys_by_value(self, collection: str, target_value: Any) -> list:
        """
        특정 value를 가진 key들을 찾기

        Args:
            collection: 컬렉션 이름
            target_value: 찾을 값

        Returns:
            해당 값을 가진 key들의 리스트
        """
        matching_keys = []

        # 1. MongoDB에서 검색 (더 효율적인 쿼리)
        if self.mongo_db is not None:
            try:
                mongo_collection = self.mongo_db[collection]
                documents = mongo_collection.find({"value": target_value})

                for doc in documents:
                    key = doc.get("_id")
                    if key:
                        matching_keys.append(key)
                        print(f"[CacheManager] Found key '{key}' with value '{target_value}' in MongoDB")

                if matching_keys:
                    print(f"[CacheManager] Found {len(matching_keys)} keys in {collection} with value '{target_value}'")
                    return matching_keys
                else:
                    print(f"[CacheManager] No keys found in MongoDB for {collection} with value '{target_value}'")
            except Exception as e:
                print(f"[CacheManager] MongoDB find_keys_by_value error: {e}")

        # 2. MongoDB가 없거나 실패한 경우 Redis에서 검색
        if self.redis:
            try:
                pattern = f"{collection}:*"
                cursor = 0

                # SCAN으로 키 패턴 검색
                while True:
                    cursor, keys = self.redis.scan(cursor, match=pattern, count=100)

                    for redis_key in keys:
                        try:
                            cached = self.redis.get(redis_key)
                            if cached is not None:
                                # JSON 파싱 시도
                                try:
                                    value = json.loads(cached)
                                except json.JSONDecodeError:
                                    value = cached

                                # 값 비교
                                if value == target_value:
                                    # Redis 키에서 collection 제거하여 실제 키만 추출
                                    actual_key = redis_key.decode('utf-8') if isinstance(redis_key, bytes) else redis_key
                                    actual_key = actual_key.replace(f"{collection}:", "", 1)
                                    if actual_key not in matching_keys:
                                        matching_keys.append(actual_key)
                                        print(f"[CacheManager] Found key '{actual_key}' with value '{target_value}' in Redis")
                        except Exception as e:
                            print(f"[CacheManager] Error checking key {redis_key}: {e}")

                    if cursor == 0:
                        break

                print(f"[CacheManager] Found {len(matching_keys)} keys in Redis for {collection} with value '{target_value}'")
            except Exception as e:
                print(f"[CacheManager] Redis find_keys_by_value error: {e}")

        if not matching_keys:
            print(f"[CacheManager] No keys found for {collection} with value '{target_value}'")

        return matching_keys

    def load_all_to_cache(self):
        """
        서버 시작 시 MongoDB의 모든 데이터를 Redis로 로드
        """
        if self.mongo_db is None or self.redis is None:
            print("[CacheManager] MongoDB or Redis not available for cache loading")
            return

        try:
            # 모든 컬렉션 조회
            collection_names = self.mongo_db.list_collection_names()
            loaded_count = 0

            for collection_name in collection_names:
                if collection_name.startswith("system."):
                    continue

                collection = self.mongo_db[collection_name]
                documents = collection.find({})

                for doc in documents:
                    key = doc.get("_id")
                    value = doc.get("value")

                    if key and value is not None:
                        redis_key = self._redis_key(collection_name, key)

                        # 해시 타입인 경우
                        if isinstance(value, dict):
                            redis_hash_key = f"{redis_key}:hash"
                            for field, field_value in value.items():
                                self.redis.hset(redis_hash_key, field, field_value)
                            self.redis.expire(redis_hash_key, 3600)
                        else:
                            # 일반 값
                            serialized = json.dumps(value) if isinstance(value, (dict, list)) else value
                            self.redis.setex(redis_key, 3600, serialized)

                        loaded_count += 1

            print(f"[CacheManager] Loaded {loaded_count} items from MongoDB to Redis")

        except Exception as e:
            print(f"[CacheManager] Error loading cache: {e}")
