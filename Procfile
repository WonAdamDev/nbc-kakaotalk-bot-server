# NBC KakaoTalk Bot - API Server
#
# PostgreSQL 단일 DB 사용 (rooms, teams, members, games)
#
# Railway 배포 방법:
# 1. 환경 변수 설정:
#    - DEBUG: False (프로덕션)
#    - DATABASE_URL: PostgreSQL 서비스의 DATABASE_URL 참조
#    - ADMIN_PASSWORD: 관리자 비밀번호
#    - JWT_SECRET_KEY: JWT 시크릿 키
#    - FRONTEND_URL: 프론트엔드 URL
# 2. 자동 배포됨
#
# Flask-SocketIO를 위해 gevent worker 사용
# -w 1: WebSocket은 stateful하므로 단일 worker 사용
# -k gevent: 비동기 이벤트 기반 worker (WebSocket 지원, Python 3.12 호환)
# --timeout 120: Worker timeout 2분 (기본 30초에서 증가)

web: gunicorn -w 1 -k gevent -b 0.0.0.0:$PORT --timeout 120 "app:create_app()"
