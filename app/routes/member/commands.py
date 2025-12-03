from flask import Blueprint, request, jsonify
from app import cache_manager

bp = Blueprint('member_commands', __name__, url_prefix='/api/commands/member')

def make_member_key(room, member):
    return f"room:{room}:member:{member}"

@bp.route('/', methods=['GET'])
def member_get_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    query_room = request.args.get('room', 'unknown')
    query_member = request.args.get('member', 'unknown')

    print(f"[MEMBER GET] Query params: room={query_room}, member={query_member}")

    try:
        member_key = make_member_key(query_room, query_member)
        member = cache_manager.get('members', member_key)

        if member:
            team_key = make_member_key(query_room, query_member)
            team = cache_manager.get('member_teams', team_key)

            if not team:
                team = "undefined"

            return jsonify({
                'success': True,
                'response': f'{query_member}님 정보\n팀: {team}'
            }), 200
        else:
            return jsonify({
                'success': True,
                'response': f'{query_member}님은 멤버가 아닙니다.'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['POST'])
def member_post_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')

    try:
        key = make_member_key(request_room, request_member)
        cache_manager.set('members', key, request_member)
        return jsonify({
            'success': True,
            'response': f'{request_member}님이 멤버가 되었습니다.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['DELETE'])
def member_delete_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER DELETE] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')

    try:
        member_key = make_member_key(request_room, request_member)
        cache_manager.delete('members', member_key)
        cache_manager.delete('member_teams', member_key)
        return jsonify({
            'success': True,
            'response': f'{request_member}님이 멤버에서 제거되었습니다.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/team/', methods=['GET'])
def member_team_get_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    request_room = request.args.get('room', 'unknown')
    request_member = request.args.get('member', 'unknown')

    print(f"[MEMBER / TEAM GET] Query params: room={request_room}, member={request_member}")

    try:
        member_key = make_member_key(request_room, request_member)
        member = cache_manager.get('members', member_key)

        if member:
            team = cache_manager.get('member_teams', member_key)

            if team:
                return jsonify({
                    'success': True,
                    'response': f'{request_member}님은 {team}팀입니다.'
                }), 200
            else:
                return jsonify({
                    'success': True,
                    'response': f'{request_member}님은 팀이 없습니다.'
                }), 200
        else:
            return jsonify({
                'success': True,
                'response': f'{request_member}님은 멤버가 아닙니다.'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/team/', methods=['POST'])
def member_team_post_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER / TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')
    request_team = data.get('team')  # 기본값 없이 가져오기

    try:
        member_key = make_member_key(request_room, request_member)
        member = cache_manager.get('members', member_key)

        if member:
            # team 파라미터가 없으면 팀 배정 삭제
            if request_team is None:
                existing_team = cache_manager.get('member_teams', member_key)
                cache_manager.delete('member_teams', member_key)
                if existing_team:
                    return jsonify({
                        'success': True,
                        'response': f'{request_member}님의 팀 배정이 삭제되었습니다.'
                    }), 200
                else:
                    return jsonify({
                        'success': True,
                        'response': f'{request_member}님은 팀에 배정되어 있지 않습니다.'
                    }), 200

            # team 파라미터가 있으면 팀 배정
            else:
                cache_manager.set('member_teams', member_key, request_team)
                return jsonify({
                    'success': True,
                    'response': f'{request_member}님이 {request_team}팀에 배정되었습니다.'
                }), 200
        else:
            return jsonify({
                'success': True,
                'response': f'{request_member}님은 멤버가 아닙니다.'
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
