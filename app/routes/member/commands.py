from flask import Blueprint, request, jsonify
from app import redis_client

bp = Blueprint('member_commands', __name__, url_prefix='/api/commands/member')

@bp.route('/team', methods=['GET'])
def member_team_get_command():
    if not redis_client:
        return jsonify({
            'success': False,
            'response': 'Redis 서버에 연결할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    user = request.args.get('target', 'unknown')
    room = request.args.get('room', 'unknown')

    try:
        key = f"room:{room}:user:{user}:team"
        team = redis_client.get(key)

        if team:
            return jsonify({
                'success': True,
                'response': f'{team}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'response': 'no team'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    

@bp.route('/team', methods=['POST'])
def member_team_post_command():
    if not redis_client:
        return jsonify({
            'success': False,
            'response': 'Redis 서버에 연결할 수 없습니다.'
        }), 500

    data = request.get_json()

    user = data.get('target', 'unknown')
    room = data.get('room', 'unknown')
    team = data.get('team', 'unknown')

    try:
        key = f"room:{room}:user:{user}:team"
        redis_client.set(key, team)

        return jsonify({
            'success': True,
            'response': f'{team}'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
