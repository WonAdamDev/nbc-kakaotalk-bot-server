from flask import Blueprint, request, jsonify
from app import cache_manager
from app.utils import generate_team_id
from app.routes.admin.auth import require_admin
from datetime import datetime
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
        # MongoDB에서 팀 조회
        mongo_db = cache_manager.mongo_db
        team_id = None
        team_found = False

        if mongo_db is not None:
            team_doc = mongo_db['teams'].find_one({
                'room_name': query_room,
                'name': query_team
            })
            if team_doc:
                team_id = team_doc.get('_id')
                team_found = True
        else:
            # MongoDB 없으면 Redis에서 조회
            team_key = make_team_key(query_room, query_team)
            team = cache_manager.get('teams', team_key)
            team_found = bool(team)

        if team_found:
            # 팀에 속한 멤버들 조회 (MongoDB만 지원)
            members = []
            if mongo_db is not None:
                member_docs = mongo_db['members'].find({
                    'room_name': query_room,
                    'team_id': team_id
                })
                for doc in member_docs:
                    members.append({
                        'name': doc.get('name'),
                        'member_id': doc.get('_id')
                    })

            return jsonify({
                'success': True,
                'data': {
                    'team': query_team,
                    'team_id': team_id,
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
        print(f"[TEAM GET] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['POST'])
@require_admin
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
        # MongoDB에서 중복 확인 (room_name + name으로 검색)
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            existing_team = mongo_db['teams'].find_one({
                'room_name': request_room,
                'name': request_team
            })

            if existing_team:
                return jsonify({
                    'success': False,
                    'data': {
                        'team': request_team,
                        'team_id': existing_team.get('_id'),
                        'created': False,
                        'reason': 'already_exists'
                    }
                }), 400

            # 팀 ID 발급
            team_id = generate_team_id()

            # MongoDB에 document로 저장
            team_doc = {
                '_id': team_id,
                'room_name': request_room,
                'name': request_team,
                'created_at': datetime.utcnow()
            }
            mongo_db['teams'].insert_one(team_doc)

            # Redis 캐시에도 저장 (하위 호환성)
            key = make_team_key(request_room, request_team)
            cache_manager.set('teams', key, request_team)

            print(f"[TEAM POST] Created team: {team_id} ({request_team})")

            return jsonify({
                'success': True,
                'data': {
                    'team': request_team,
                    'team_id': team_id,
                    'created': True
                }
            }), 200
        else:
            # MongoDB 없으면 기존 방식 사용
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

            cache_manager.set('teams', key, request_team)
            return jsonify({
                'success': True,
                'data': {
                    'team': request_team,
                    'created': True
                }
            }), 200

    except Exception as e:
        print(f"[TEAM POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['DELETE'])
@require_admin
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
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            # MongoDB에서 팀 확인
            team_doc = mongo_db['teams'].find_one({
                'room_name': request_room,
                'name': request_team
            })

            if not team_doc:
                return jsonify({
                    'success': False,
                    'data': {
                        'team': request_team,
                        'deleted': False,
                        'reason': 'not_found'
                    }
                }), 404

            team_id = team_doc.get('_id')

            # 팀에 배정된 멤버가 있는지 확인
            member_count = mongo_db['members'].count_documents({
                'room_name': request_room,
                'team_id': team_id
            })

            if member_count > 0:
                # 멤버가 있으면 삭제 거부
                return jsonify({
                    'success': False,
                    'data': {
                        'team': request_team,
                        'deleted': False,
                        'reason': 'has_members',
                        'member_count': member_count
                    }
                }), 400

            # 멤버가 없으면 팀 삭제
            mongo_db['teams'].delete_one({'_id': team_id})

            return jsonify({
                'success': True,
                'data': {
                    'team': request_team,
                    'team_id': team_id,
                    'deleted': True
                }
            }), 200
        else:
            # MongoDB 없으면 기존 Redis 방식
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

            # 멤버가 없으면 팀 삭제
            cache_manager.delete('teams', team_key)

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
                # 새 구조: room_name 필드로 검색
                mongo_collection = cache_manager.mongo_db['teams']
                documents = mongo_collection.find({
                    'room_name': query_room
                })

                for doc in documents:
                    team_id = doc.get('_id')
                    team_name = doc.get('name')

                    # 팀에 속한 멤버 수 조회
                    member_count = cache_manager.mongo_db['members'].count_documents({
                        'room_name': query_room,
                        'team_id': team_id
                    })

                    teams.append({
                        'name': team_name,
                        'team_id': team_id,
                        'room': query_room,
                        'member_count': member_count
                    })

                print(f"[TEAM LIST] Found {len(teams)} teams in room '{query_room}'")

            except Exception as e:
                print(f"[TEAM LIST] MongoDB error: {e}")

        # 중복 제거 및 정렬
        unique_teams = {t['team_id']: t for t in teams}.values()
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
        print(f"[TEAM LIST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
