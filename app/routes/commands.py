from flask import Blueprint, request, jsonify
from app import redis_client

bp = Blueprint('commands', __name__, url_prefix='/api/commands')

@bp.route('/echo', methods=['POST'])
def echo_command():
    """
    에코 명령어 처리
    카카오톡 봇에서 !echo <메시지> 형태로 받아서 처리
    """
    data = request.get_json()
    print(f"[ECHO] Received JSON: {data}")

    message = data.get('message', '')

    return jsonify({
        'success': True,
        'response': message
    }), 200
