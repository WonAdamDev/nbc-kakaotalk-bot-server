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
            'message': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    query_room = request.args.get('room', 'unknown')
    query_member = request.args.get('member', 'unknown')

    print(f"[MEMBER GET] Query params: room={query_room}, member={query_member}")

    try:
        member_key = make_member_key(query_room, query_member)
        member = cache_manager.get('members', member_key)

        if member:
            team = cache_manager.get('member_teams', member_key)

            return jsonify({
                'success': True,
                'data': {
                    'member': query_member,
                    'team': team,
                    'exists': True
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'data': {
                    'member': query_member,
                    'exists': False
                }
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['POST'])
def member_post_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
            'data': {
                'member': request_member
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['DELETE'])
def member_delete_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
            'data': {
                'member': request_member
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
