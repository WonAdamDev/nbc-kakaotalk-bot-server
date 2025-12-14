"""
Admin 인증 미들웨어 및 유틸리티
"""
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta


def generate_token():
    """JWT 토큰 생성"""
    expires_seconds = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    payload = {
        'role': 'admin',
        'exp': datetime.utcnow() + timedelta(seconds=expires_seconds)
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return token


def verify_token(token):
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_admin(f):
    """관리자 인증 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # OPTIONS 요청은 인증 없이 통과 (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            print(f"[AUTH] No Authorization header for {request.method} {request.path}")
            return jsonify({
                'success': False,
                'message': '인증 토큰이 필요합니다.'
            }), 401

        try:
            # Bearer 토큰 형식 확인
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                print(f"[AUTH] Invalid token type: {token_type}")
                return jsonify({
                    'success': False,
                    'message': '올바른 토큰 형식이 아닙니다.'
                }), 401
        except ValueError:
            print(f"[AUTH] Invalid Authorization header format")
            return jsonify({
                'success': False,
                'message': '올바른 토큰 형식이 아닙니다.'
            }), 401

        # 토큰 검증
        payload = verify_token(token)
        if not payload:
            print(f"[AUTH] Invalid or expired token")
            return jsonify({
                'success': False,
                'message': '유효하지 않거나 만료된 토큰입니다.'
            }), 401

        # role 확인
        if payload.get('role') != 'admin':
            print(f"[AUTH] Invalid role: {payload.get('role')}")
            return jsonify({
                'success': False,
                'message': '관리자 권한이 필요합니다.'
            }), 403

        print(f"[AUTH] Admin authenticated for {request.method} {request.path}")
        return f(*args, **kwargs)

    return decorated_function
