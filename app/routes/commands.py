from flask import Blueprint, request, jsonify

bp = Blueprint('commands', __name__, url_prefix='/api/commands')


@bp.route('/test', methods=['POST'])
def test_command():
    """
    테스트 명령어 처리
    카카오톡 봇에서 !test 명령어를 파싱하고 이 엔드포인트로 요청
    """
    data = request.get_json()

    return jsonify({
        'success': True,
        'message': '테스트 명령어가 성공적으로 처리되었습니다.',
        'data': data
    }), 200


@bp.route('/echo', methods=['POST'])
def echo_command():
    """
    에코 명령어 처리
    카카오톡 봇에서 !echo <메시지> 형태로 받아서 처리
    """
    data = request.get_json()
    message = data.get('message', '')

    return jsonify({
        'success': True,
        'response': message
    }), 200


# 여기에 추가 명령어 엔드포인트를 추가하세요
# 예: @bp.route('/weather', methods=['POST'])
#     @bp.route('/translate', methods=['POST'])
#     등등
