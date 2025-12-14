"""
Admin 관련 API 엔드포인트
"""
from flask import Blueprint, request, jsonify, current_app
from app.routes.admin.auth import generate_token, require_admin
from app import redis_client

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# 로그인 시도 제한 설정
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15분 (초 단위)


def get_client_ip():
    """클라이언트 IP 주소 가져오기 (프록시 고려)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


def get_login_attempt_key(ip):
    """로그인 시도 횟수 저장 키 생성"""
    return f"admin_login_attempts:{ip}"


def is_locked_out(ip):
    """로그인 차단 상태 확인"""
    if not redis_client:
        return False

    key = get_login_attempt_key(ip)
    attempts = redis_client.get(key)

    if attempts and int(attempts) >= MAX_LOGIN_ATTEMPTS:
        return True
    return False


def increment_login_attempts(ip):
    """로그인 시도 횟수 증가"""
    if not redis_client:
        return

    key = get_login_attempt_key(ip)
    current = redis_client.get(key)

    if current:
        attempts = int(current) + 1
        redis_client.setex(key, LOCKOUT_DURATION, attempts)
    else:
        redis_client.setex(key, LOCKOUT_DURATION, 1)

    print(f"[ADMIN LOGIN] IP {ip} - 로그인 시도 횟수: {redis_client.get(key)}/{MAX_LOGIN_ATTEMPTS}")


def reset_login_attempts(ip):
    """로그인 시도 횟수 초기화"""
    if not redis_client:
        return

    key = get_login_attempt_key(ip)
    redis_client.delete(key)
    print(f"[ADMIN LOGIN] IP {ip} - 로그인 성공, 시도 횟수 초기화")


def get_remaining_attempts(ip):
    """남은 로그인 시도 횟수 반환"""
    if not redis_client:
        return MAX_LOGIN_ATTEMPTS

    key = get_login_attempt_key(ip)
    attempts = redis_client.get(key)

    if attempts:
        return MAX_LOGIN_ATTEMPTS - int(attempts)
    return MAX_LOGIN_ATTEMPTS


@bp.route('/login', methods=['POST'])
def login():
    """
    관리자 로그인 (비밀번호만 입력)
    Body: {
        "password": "admin123"
    }
    """
    client_ip = get_client_ip()

    # 로그인 차단 확인
    if is_locked_out(client_ip):
        print(f"[ADMIN LOGIN] IP {client_ip} - 로그인 차단됨 (최대 시도 횟수 초과)")
        return jsonify({
            'success': False,
            'message': f'로그인 시도 횟수를 초과했습니다. {LOCKOUT_DURATION // 60}분 후에 다시 시도해주세요.'
        }), 429  # Too Many Requests

    data = request.get_json()
    password = data.get('password')

    # 입력값 검증
    if not password:
        return jsonify({
            'success': False,
            'message': '비밀번호를 입력해주세요.'
        }), 400

    # 비밀번호 확인
    if password != current_app.config['ADMIN_PASSWORD']:
        increment_login_attempts(client_ip)
        remaining = get_remaining_attempts(client_ip)

        if remaining > 0:
            return jsonify({
                'success': False,
                'message': f'비밀번호가 올바르지 않습니다. (남은 시도: {remaining}회)'
            }), 401
        else:
            return jsonify({
                'success': False,
                'message': f'로그인 시도 횟수를 초과했습니다. {LOCKOUT_DURATION // 60}분 후에 다시 시도해주세요.'
            }), 429

    # 로그인 성공 - 시도 횟수 초기화
    reset_login_attempts(client_ip)

    # 토큰 생성
    token = generate_token()

    return jsonify({
        'success': True,
        'message': '로그인 성공',
        'token': token
    }), 200


@bp.route('/verify', methods=['POST'])
def verify_token():
    """
    토큰 유효성 검증
    Body: {
        "token": "jwt_token_here"
    }
    """
    from app.routes.admin.auth import verify_token as verify

    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({
            'success': False,
            'message': '토큰을 입력해주세요.'
        }), 400

    payload = verify(token)

    if not payload:
        return jsonify({
            'success': False,
            'message': '유효하지 않거나 만료된 토큰입니다.'
        }), 401

    return jsonify({
        'success': True,
        'message': '유효한 토큰입니다.'
    }), 200
