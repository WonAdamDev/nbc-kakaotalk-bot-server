from flask import Blueprint, request, jsonify
from app import cache_manager
from app.utils import generate_member_id
from app.routes.admin.auth import require_admin
from datetime import datetime
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
    query_member_id = request.args.get('member_id')  # 선택적 파라미터

    print(f"[MEMBER GET] Query params: room={query_room}, member={query_member}, member_id={query_member_id}")

    try:
        # MongoDB에서 멤버 조회
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            # member_id가 제공된 경우 ID로 조회
            if query_member_id:
                member_doc = mongo_db['members'].find_one({
                    '_id': query_member_id,
                    'room_name': query_room
                })

                if member_doc:
                    team_id = member_doc.get('team_id')
                    team_name = None
                    if team_id:
                        team_doc = mongo_db['teams'].find_one({'_id': team_id})
                        if team_doc:
                            team_name = team_doc.get('name')

                    return jsonify({
                        'success': True,
                        'data': {
                            'member': member_doc.get('name'),
                            'member_id': member_doc.get('_id'),
                            'team': team_name,
                            'team_id': team_id,
                            'exists': True,
                            'is_unique': True
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

            # 이름으로 조회 (동명이인 체크)
            member_docs = list(mongo_db['members'].find({
                'room_name': query_room,
                'name': query_member
            }))

            if len(member_docs) == 0:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': query_member,
                        'exists': False
                    }
                }), 404
            elif len(member_docs) == 1:
                # 동명이인 없음
                member_doc = member_docs[0]
                member_id = member_doc.get('_id')
                team_id = member_doc.get('team_id')

                # 팀 이름 조회
                team_name = None
                if team_id:
                    team_doc = mongo_db['teams'].find_one({'_id': team_id})
                    if team_doc:
                        team_name = team_doc.get('name')

                return jsonify({
                    'success': True,
                    'data': {
                        'member': query_member,
                        'member_id': member_id,
                        'team': team_name,
                        'team_id': team_id,
                        'exists': True,
                        'is_unique': True
                    }
                }), 200
            else:
                # 동명이인 있음
                duplicates = []
                for doc in member_docs:
                    team_id = doc.get('team_id')
                    team_name = None
                    if team_id:
                        team_doc = mongo_db['teams'].find_one({'_id': team_id})
                        if team_doc:
                            team_name = team_doc.get('name')

                    duplicates.append({
                        'member_id': doc.get('_id'),
                        'team': team_name,
                        'team_id': team_id
                    })

                return jsonify({
                    'success': True,
                    'data': {
                        'member': query_member,
                        'exists': True,
                        'is_unique': False,
                        'duplicates': duplicates,
                        'count': len(duplicates)
                    }
                }), 200
        else:
            # MongoDB 없으면 Redis에서 조회
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
        print(f"[MEMBER GET] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['POST'])
@require_admin
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
        # MongoDB에서 중복 확인
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            existing_member = mongo_db['members'].find_one({
                'room_name': request_room,
                'name': request_member
            })

            if existing_member:
                return jsonify({
                    'success': True,
                    'data': {
                        'member': request_member,
                        'member_id': existing_member.get('_id'),
                        'team_id': existing_member.get('team_id'),
                        'already_exists': True
                    }
                }), 200

            # 멤버 ID 발급
            member_id = generate_member_id()

            # MongoDB에 document로 저장
            member_doc = {
                '_id': member_id,
                'room_name': request_room,
                'name': request_member,
                'team_id': None,  # 초기에는 팀 미배정
                'created_at': datetime.utcnow()
            }
            mongo_db['members'].insert_one(member_doc)

            # Redis 캐시에도 저장 (하위 호환성)
            key = make_member_key(request_room, request_member)
            cache_manager.set('members', key, request_member)

            print(f"[MEMBER POST] Created member: {member_id} ({request_member})")

            return jsonify({
                'success': True,
                'data': {
                    'member': request_member,
                    'member_id': member_id,
                    'team_id': None,
                    'already_exists': False
                }
            }), 200
        else:
            # MongoDB 없으면 기존 방식 사용
            key = make_member_key(request_room, request_member)
            cache_manager.set('members', key, request_member)
            return jsonify({
                'success': True,
                'data': {
                    'member': request_member
                }
            }), 200

    except Exception as e:
        print(f"[MEMBER POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
    
@bp.route('/', methods=['DELETE'])
@require_admin
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
    request_member_id = data.get('member_id')  # 선택적 파라미터

    try:
        mongo_db = cache_manager.mongo_db
        if mongo_db is not None:
            # member_id가 제공된 경우
            if request_member_id:
                result = mongo_db['members'].delete_one({
                    '_id': request_member_id,
                    'room_name': request_room
                })
                if result.deleted_count > 0:
                    return jsonify({
                        'success': True,
                        'data': {
                            'member': request_member,
                            'member_id': request_member_id,
                            'deleted': True
                        }
                    }), 200
                else:
                    return jsonify({
                        'success': False,
                        'message': '멤버를 찾을 수 없습니다.'
                    }), 404

            # 이름만 제공된 경우 - 동명이인 체크
            member_docs = list(mongo_db['members'].find({
                'room_name': request_room,
                'name': request_member
            }))

            if len(member_docs) == 0:
                return jsonify({
                    'success': False,
                    'message': '멤버를 찾을 수 없습니다.',
                    'data': {
                        'member': request_member,
                        'exists': False
                    }
                }), 404
            elif len(member_docs) > 1:
                # 동명이인 있음
                duplicates = []
                for doc in member_docs:
                    team_id = doc.get('team_id')
                    team_name = None
                    if team_id:
                        team_doc = mongo_db['teams'].find_one({'_id': team_id})
                        if team_doc:
                            team_name = team_doc.get('name')

                    duplicates.append({
                        'member_id': doc.get('_id'),
                        'team': team_name
                    })

                return jsonify({
                    'success': False,
                    'message': '동명이인이 존재합니다. member_id를 지정해주세요.',
                    'data': {
                        'member': request_member,
                        'is_unique': False,
                        'duplicates': duplicates,
                        'count': len(duplicates)
                    }
                }), 409

            # 동명이인 없음 - 삭제
            result = mongo_db['members'].delete_one({
                '_id': member_docs[0]['_id']
            })

            if result.deleted_count > 0:
                # Redis 캐시에서도 삭제
                member_key = make_member_key(request_room, request_member)
                cache_manager.delete('members', member_key)
                cache_manager.delete('member_teams', member_key)

                return jsonify({
                    'success': True,
                    'data': {
                        'member': request_member,
                        'member_id': member_docs[0]['_id'],
                        'deleted': True
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': '삭제 실패'
                }), 500
        else:
            # MongoDB 없으면 기존 방식
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
        print(f"[MEMBER DELETE] Error: {e}")
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
                # 새 구조: room_name 필드로 검색
                mongo_collection = cache_manager.mongo_db['members']
                documents = mongo_collection.find({
                    'room_name': query_room
                })

                for doc in documents:
                    member_id = doc.get('_id')
                    member_name = doc.get('name')
                    team_id = doc.get('team_id')

                    # 팀 이름 조회
                    team_name = None
                    if team_id:
                        team_doc = cache_manager.mongo_db['teams'].find_one({'_id': team_id})
                        if team_doc:
                            team_name = team_doc.get('name')

                    members.append({
                        'name': member_name,
                        'member_id': member_id,
                        'room': query_room,
                        'team': team_name,
                        'team_id': team_id
                    })

                print(f"[MEMBER LIST] Found {len(members)} members in room '{query_room}'")

            except Exception as e:
                print(f"[MEMBER LIST] MongoDB error: {e}")

        # 중복 제거 및 정렬
        unique_members = {m['member_id']: m for m in members}.values()
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
        print(f"[MEMBER LIST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
