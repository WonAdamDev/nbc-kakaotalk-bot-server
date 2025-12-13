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
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
                'data': {
                    'member': request_member,
                    'is_member': False
                }
            }), 404

        # 팀 배정 조회
        team = cache_manager.get('member_teams', member_key)

        return jsonify({
            'success': True,
            'data': {
                'member': request_member,
                'team': team,
                'is_member': True
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['POST'])
def member_team_post_command():
    """멤버를 팀에 배정"""
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
        }), 500

    data = request.get_json()
    print(f"[MEMBER_TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')
    request_team = data.get('team')

    if not request_team:
        return jsonify({
            'success': False,
            'message': '팀 이름을 입력해주세요.'
        }), 400

    try:
        # MongoDB에서 처리
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            # 멤버 존재 확인
            member_doc = mongo_db['members'].find_one({
                'room_name': request_room,
                'name': request_member
            })
            if not member_doc:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404

            # 팀 존재 확인 및 team_id 가져오기
            team_doc = mongo_db['teams'].find_one({
                'room_name': request_room,
                'name': request_team
            })
            if not team_doc:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'team_not_found'
                    }
                }), 404

            team_id = team_doc.get('_id')

            # MongoDB에서 멤버의 team_id 업데이트
            mongo_db['members'].update_one(
                {'_id': member_doc['_id']},
                {'$set': {'team_id': team_id}}
            )

            # Redis 캐시에도 저장 (하위 호환성)
            member_key = make_member_key(request_room, request_member)
            cache_manager.set('member_teams', member_key, request_team)

            print(f"[MEMBER_TEAM POST] Assigned {request_member} to team {request_team} (ID: {team_id})")

            return jsonify({
                'success': True,
                'data': {
                    'member': request_member,
                    'member_id': member_doc['_id'],
                    'team': request_team,
                    'team_id': team_id,
                    'assigned': True
                }
            }), 200
        else:
            # MongoDB 없으면 기존 방식 사용
            member_key = make_member_key(request_room, request_member)

            # 멤버가 존재하는지 확인
            member = cache_manager.get('members', member_key)
            if not member:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404

            # 팀이 존재하는지 확인
            team_key = f"room:{request_room}:team:{request_team}"
            team = cache_manager.get('teams', team_key)
            if not team:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'team_not_found'
                    }
                }), 404

            # 팀 배정
            cache_manager.set('member_teams', member_key, request_team)

            return jsonify({
                'success': True,
                'data': {
                    'member': request_member,
                    'team': request_team,
                    'assigned': True
                }
            }), 200

    except Exception as e:
        print(f"[MEMBER_TEAM POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['DELETE'])
def member_team_delete_command():
    """멤버의 팀 배정 해제"""
    if not cache_manager:
        return jsonify({
            'success': False,
            'message': '캐시 시스템을 사용할 수 없습니다.'
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
                'data': {
                    'member': request_member,
                    'unassigned': False,
                    'reason': 'member_not_found'
                }
            }), 404

        # 팀 배정이 있는지 확인
        existing_team = cache_manager.get('member_teams', member_key)

        if not existing_team:
            return jsonify({
                'success': False,
                'data': {
                    'member': request_member,
                    'unassigned': False,
                    'reason': 'no_team_assigned'
                }
            }), 400

        # 팀 배정 삭제
        cache_manager.delete('member_teams', member_key)

        return jsonify({
            'success': True,
            'data': {
                'member': request_member,
                'previous_team': existing_team,
                'unassigned': True
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
