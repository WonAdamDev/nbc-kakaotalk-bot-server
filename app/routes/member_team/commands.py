from flask import Blueprint, request, jsonify
from app import cache_manager

bp = Blueprint('member_team_commands', __name__, url_prefix='/api/commands/member_team')

def make_member_key(room, member):
    """멤버 키 생성 헬퍼 함수"""
    return f"room:{room}:member:{member}"

@bp.route('/', methods=['GET'])
def member_team_get_command():
    """멤버의 팀 배정 조회"""
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    request_room = request.args.get('room', 'unknown')
    request_member = request.args.get('member', 'unknown')

    print(f"[MEMBER_TEAM GET] Query params: room={request_room}, member={request_member}")

    try:
        member_key = make_member_key(request_room, request_member)

        # 멤버가 존재하는지 확인
        member = cache_manager.get('members', member_key)
        if not member:
            return jsonify({
                'success': False,
                'response': f'{request_member}님은 멤버가 아닙니다.'
            }), 404

        # 팀 배정 조회
        team = cache_manager.get('member_teams', member_key)

        if team:
            return jsonify({
                'success': True,
                'response': f'{request_member}님은 {team}팀에 배정되어 있습니다.'
            }), 200
        else:
            return jsonify({
                'success': True,
                'response': f'{request_member}님은 팀에 배정되어 있지 않습니다.'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['POST'])
def member_team_post_command():
    """멤버를 팀에 배정"""
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER_TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')
    request_team = data.get('team')

    if not request_team:
        return jsonify({
            'success': False,
            'response': '팀 이름을 입력해주세요.'
        }), 400

    try:
        member_key = make_member_key(request_room, request_member)

        # 멤버가 존재하는지 확인
        member = cache_manager.get('members', member_key)
        if not member:
            return jsonify({
                'success': False,
                'response': f'{request_member}님은 멤버가 아닙니다.'
            }), 404

        # 팀이 존재하는지 확인
        team_key = f"room:{request_room}:team:{request_team}"
        team = cache_manager.get('teams', team_key)
        if not team:
            return jsonify({
                'success': False,
                'response': f'{request_team}팀은 존재하지 않습니다.'
            }), 404

        # 팀 배정
        cache_manager.set('member_teams', member_key, request_team)

        return jsonify({
            'success': True,
            'response': f'{request_member}님이 {request_team}팀에 배정되었습니다.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['DELETE'])
def member_team_delete_command():
    """멤버의 팀 배정 해제"""
    if not cache_manager:
        return jsonify({
            'success': False,
            'response': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER_TEAM DELETE] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')

    try:
        member_key = make_member_key(request_room, request_member)

        # 멤버가 존재하는지 확인
        member = cache_manager.get('members', member_key)
        if not member:
            return jsonify({
                'success': False,
                'response': f'{request_member}님은 멤버가 아닙니다.'
            }), 404

        # 팀 배정이 있는지 확인
        existing_team = cache_manager.get('member_teams', member_key)

        if not existing_team:
            return jsonify({
                'success': True,
                'response': f'{request_member}님은 팀에 배정되어 있지 않습니다.'
            }), 200

        # 팀 배정 삭제
        cache_manager.delete('member_teams', member_key)

        return jsonify({
            'success': True,
            'response': f'{request_member}님의 팀 배정({existing_team})이 해제되었습니다.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'오류가 발생했습니다: {str(e)}'
        }), 500
