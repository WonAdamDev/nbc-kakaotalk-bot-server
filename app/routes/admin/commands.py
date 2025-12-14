"""
Admin 관련 API 엔드포인트
"""
from flask import Blueprint, request, jsonify, current_app
from app.routes.admin.auth import generate_token, require_admin

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/login', methods=['POST'])
def login():
    """
    관리자 로그인 (비밀번호만 입력)
    Body: {
        "password": "admin123"
    }
    """
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
        return jsonify({
            'success': False,
            'message': '비밀번호가 올바르지 않습니다.'
        }), 401

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
