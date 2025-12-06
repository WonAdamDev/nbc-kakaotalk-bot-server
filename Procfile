# NBC KakaoTalk Bot - API Server
#
# Seed 기능은 별도의 db-seeder 서비스로 분리되었습니다.
# 서버는 API 처리만 담당합니다.
#
# Railway 배포 방법:
# 1. 환경 변수 설정:
#    - SECRET_KEY: 랜덤 문자열
#    - DEBUG: False (프로덕션)
#    - REDIS_URL: Redis 서비스의 REDIS_URL 참조
#    - MONGO_URI: MongoDB 서비스의 MONGO_URI 참조
#    - MONGO_DB_NAME: nbc_kakaotalk_bot
# 2. 자동 배포됨

web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
