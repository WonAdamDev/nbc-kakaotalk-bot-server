from flask import Blueprint, request, jsonify
from app import cache_manager
import re

bp = Blueprint('team_commands', __name__, url_prefix='/api/commands/team')

def make_team_key(room, team):
    return f"room:{room}:team:{team}"

def extract_room_and_team_from_key(key):
    """키에서 room과 team 추출: room:{room}:team:{team}"""
    match = re.match(r'room:(.+?):team:(.+)', key)
    if match:
        return match.group(1), match.group(2)
    return None, None

@bp.route('/', methods=['GET'])
def team_get_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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

            # 키에서 멤버 이름만 추출
            members = []
            for key in member_keys:
                # "room:A:member:철수" → "철수"
                member_name = key.split(':')[-1]
                members.append(member_name)

            return jsonify({
                'success': True,
                'data': {
                    'team': query_team,
                    'member_count': len(members),
                    'members': members,
                    'exists': True
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'data': {
                    'team': query_team,
                    'exists': False
                }
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['POST'])
def team_post_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
                'success': False,
                'data': {
                    'team': request_team,
                    'created': False,
                    'reason': 'already_exists'
                }
            }), 400
        else:
            cache_manager.set('teams', key, request_team)
            return jsonify({
                'success': True,
                'data': {
                    'team': request_team,
                    'created': True
                }
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['DELETE'])
def team_delete_command():
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
                'success': False,
                'data': {
                    'team': request_team,
                    'deleted': False,
                    'reason': 'not_found'
                }
            }), 404

        # 팀에 배정된 멤버가 있는지 확인
        member_keys = cache_manager.find_keys_by_value('member_teams', request_team)

        if member_keys:
            # 멤버가 있으면 삭제 거부
            member_count = len(member_keys)
            return jsonify({
                'success': False,
                'data': {
                    'team': request_team,
                    'deleted': False,
                    'reason': 'has_members',
                    'member_count': member_count
                }
            }), 400
        else:
            # 멤버가 없으면 팀 삭제
            cache_manager.delete('teams', team_key)

            # 안전을 위해 혹시 남아있을 수 있는 member_teams 정리
            # (고아 데이터 방지)
            member_keys_cleanup = cache_manager.find_keys_by_value('member_teams', request_team)
            for member_key in member_keys_cleanup:
                cache_manager.delete('member_teams', member_key)
                print(f"[TEAM DELETE] Cleaned up orphaned member_team: {member_key}")

            return jsonify({
                'success': True,
                'data': {
                    'team': request_team,
                    'deleted': True
                }
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500


@bp.route('/list', methods=['GET'])
def team_list_command():
    """
    특정 방의 모든 팀 조회
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
        teams = []

        # MongoDB에서 해당 방의 모든 팀 조회
        if cache_manager.mongo_db is not None:
            try:
                # teams 컬렉션에서 해당 방의 팀 찾기
                # 키 패턴: room:{room}:team:{team}
                pattern_prefix = f"room:{query_room}:team:"

                mongo_collection = cache_manager.mongo_db['teams']
                documents = mongo_collection.find({
                    "_id": {"$regex": f"^{re.escape(pattern_prefix)}"}
                })

                for doc in documents:
                    key = doc.get("_id")
                    if key:
                        room, team_name = extract_room_and_team_from_key(key)
                        if room == query_room and team_name:
                            # 팀에 속한 멤버 수 조회
                            member_keys = cache_manager.find_keys_by_value('member_teams', team_name)
                            member_count = len(member_keys)

                            teams.append({
                                'name': team_name,
                                'room': room,
                                'member_count': member_count
                            })

                print(f"[TEAM LIST] Found {len(teams)} teams in room '{query_room}'")

            except Exception as e:
                print(f"[TEAM LIST] MongoDB error: {e}")

        # 중복 제거 및 정렬
        unique_teams = {t['name']: t for t in teams}.values()
        sorted_teams = sorted(unique_teams, key=lambda x: x['name'])

        return jsonify({
            'success': True,
            'data': {
                'room': query_room,
                'teams': sorted_teams,
                'count': len(sorted_teams)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
