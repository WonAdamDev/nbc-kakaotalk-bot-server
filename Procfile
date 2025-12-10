# NBC KakaoTalk Bot - API Server
#
# Seed 기능은 별도의 db-seeder 서비스로 분리되었습니다.
# 서버는 API 처리만 담당합니다.
#
# Railway 배포 방법:
# 1. 환경 변수 설정:
#    - DEBUG: False (프로덕션)
#    - REDIS_URL: Redis 서비스의 REDIS_URL 참조
#    - MONGO_URI: MongoDB 서비스의 MONGO_URI 참조
#    - MONGO_DB_NAME: nbc_kakaotalk_bot
# 2. 자동 배포됨
#
# Flask-SocketIO를 위해 gevent worker 사용
# -w 1: WebSocket은 stateful하므로 단일 worker 사용
# -k gevent: 비동기 이벤트 기반 worker (WebSocket 지원, Python 3.12 호환)
# --timeout 120: Worker timeout 2분 (기본 30초에서 증가)

web: gunicorn -w 1 -k gevent -b 0.0.0.0:$PORT --timeout 120 "app:create_app()"
