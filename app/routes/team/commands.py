from flask import Blueprint, request, jsonify
from app import cache_manager

bp = Blueprint('team_commands', __name__, url_prefix='/api/commands/team')

def make_team_key(room, team):
    return f"room:{room}:team:{team}"

@bp.route('/', methods=['GET'])
def team_get_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    query_room = request.args.get('room', 'unknown')
    query_team = request.args.get('team', 'unknown')

    print(f"[TEAM GET] Query params: room={query_room}, team={query_team}")

    try:
        team_key = make_team_key(query_room, query_team)
        team = cache_manager.get('teams', team_key)

        if team:
            # 팀에 속한 멤버들 조회
            member_keys = cache_manager.find_keys_by_value('member_teams', query_team)

            if member_keys:
                # 키에서 멤버 이름만 추출
                members = []
                for key in member_keys:
                    # "room:A:member:철수" → "철수"
                    member_name = key.split(':')[-1]
                    members.append(member_name)

                member_list = ', '.join(members)
                return jsonify({
                    'success': True,
                    'response': f'{query_team}팀 정보\n멤버 수: {len(members)}명\n멤버: {member_list}'
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'response': f'{query_team}팀 정보\n멤버 수: 0명'
                }), 200
        else:
            return jsonify({
                'success': True,
                'response': f'{query_team}팀은 존재하지 않습니다.'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['POST'])
def team_post_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_team = data.get('team', 'unknown')

    try:
        key = make_team_key(request_room, request_team)
        team = cache_manager.get('teams', key)

        if team:
            return jsonify({
                'success': True,
                'response': f'{request_team}팀이 이미 존재합니다.'
            }), 200
        else:
            cache_manager.set('teams', key, request_team)
            return jsonify({
                'success': True,
                'response': f'{request_team}팀이 생성되었습니다.'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['DELETE'])
def team_delete_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[TEAM DELETE] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_team = data.get('team', 'unknown')

    try:
        team_key = make_team_key(request_room, request_team)
        team = cache_manager.get('teams', team_key)

        if not team:
            return jsonify({
                'success': True,
                'response': f'{request_team}팀은 존재하지 않습니다.'
            }), 200

        # 팀에 배정된 멤버가 있는지 확인
        member_keys = cache_manager.find_keys_by_value('member_teams', request_team)

        if member_keys:
            # 멤버가 있으면 삭제 거부
            member_count = len(member_keys)
            return jsonify({
                'success': False,
                'response': f'{request_team}팀에 {member_count}명의 멤버가 있어 삭제할 수 없습니다.'
            }), 400
        else:
            # 멤버가 없으면 팀 삭제
            cache_manager.delete('teams', team_key)
            return jsonify({
                'success': True,
                'response': f'{request_team}팀이 삭제되었습니다.'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
