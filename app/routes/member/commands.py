from flask import Blueprint, request, jsonify
from app import cache_manager
import re

bp = Blueprint('member_commands', __name__, url_prefix='/api/commands/member')

def make_member_key(room, member):
    return f"room:{room}:member:{member}"

def extract_room_and_member_from_key(key):
    """키에서 room과 member 추출: room:{room}:member:{member}"""
    match = re.match(r'room:(.+?):member:(.+)', key)
    if match:
        return match.group(1), match.group(2)
    return None, None

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


@bp.route('/list', methods=['GET'])
def member_list_command():
    """
    특정 방의 모든 멤버 조회
    Query params: room=방이름
    """
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    query_room = request.args.get('room')
    if not query_room:
        return jsonify({
            'success': False,
            'message': 'room parameter is required'
        }), 400

    try:
        members = []

        # MongoDB에서 해당 방의 모든 멤버 조회
        if cache_manager.mongo_db is not None:
            try:
                # members 컬렉션에서 해당 방의 멤버 찾기
                # 키 패턴: room:{room}:member:{member}
                pattern_prefix = f"room:{query_room}:member:"

                mongo_collection = cache_manager.mongo_db['members']
                documents = mongo_collection.find({
                    "_id": {"$regex": f"^{re.escape(pattern_prefix)}"}
                })

                for doc in documents:
                    key = doc.get("_id")
                    if key:
                        room, member_name = extract_room_and_member_from_key(key)
                        if room == query_room and member_name:
                            # 멤버의 팀 정보도 조회
                            team = cache_manager.get('member_teams', key)
                            members.append({
                                'name': member_name,
                                'room': room,
                                'team': team  # 팀 정보 추가 (None일 수 있음)
                            })

                print(f"[MEMBER LIST] Found {len(members)} members in room '{query_room}'")

            except Exception as e:
                print(f"[MEMBER LIST] MongoDB error: {e}")

        # 중복 제거 및 정렬
        unique_members = {m['name']: m for m in members}.values()
        sorted_members = sorted(unique_members, key=lambda x: x['name'])

        return jsonify({
            'success': True,
            'data': {
                'room': query_room,
                'members': sorted_members,
                'count': len(sorted_members)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
