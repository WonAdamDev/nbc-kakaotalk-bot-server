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

    print(f"[TEAM GET] Query params: target={user}, room={room}")

    try:
        key = f"room:{room}:user:{user}:team"
        team = redis_client.get(key)

        if team:
            return jsonify({
                'success': True,
                'response': f'{user}님은 {team}팀입니다.'
            }), 200
        else:
            return jsonify({
                'success': False,
                'response': f'{user}님은 팀이 없습니다.'
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
    print(f"[TEAM POST] Received JSON: {data}")

    user = data.get('target', 'unknown')
    room = data.get('room', 'unknown')
    team = data.get('team')  # 기본값 없이 가져오기

    try:
        key = f"room:{room}:user:{user}:team"

        # team 파라미터가 없으면 팀 배정 삭제
        if team is None:
            deleted = redis_client.delete(key)
            if deleted:
                return jsonify({
                    'success': True,
                    'response': f'{user}님의 팀 배정이 삭제되었습니다.'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'response': f'{user}님은 팀에 배정되어 있지 않습니다.'
                }), 200

        # team 파라미터가 있으면 팀 배정
        else:
            redis_client.set(key, team)
            return jsonify({
                'success': True,
                'response': f'{user}님이 {team}팀에 배정되었습니다.'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
