from flask import Blueprint, request, jsonify
from app.models import db, Room, Member, Team
from app.utils import generate_member_id
from app.routes.admin.auth import require_admin
from datetime import datetime

bp = Blueprint('member_commands', __name__, url_prefix='/api/commands/member')

@bp.route('/', methods=['GET'])
def member_get_command():
    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    query_room = request.args.get('room', 'unknown')
    query_member = request.args.get('member', 'unknown')
    query_member_id = request.args.get('member_id')

    print(f"[MEMBER GET] Query params: room={query_room}, member={query_member}, member_id={query_member_id}")

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=query_room).first()
        if not room:
            return jsonify({
                'success': False,
                'data': {
                    'member': query_member,
                    'exists': False
                }
            }), 404

        # member_id가 제공된 경우 ID로 조회
        if query_member_id:
            member = Member.query.filter_by(
                member_id=query_member_id,
                room_id=room.room_id
            ).first()

            if member:
                team_name = None
                if member.team_id:
                    team = Team.query.filter_by(team_id=member.team_id).first()
                    if team:
                        team_name = team.name

                return jsonify({
                    'success': True,
                    'data': {
                        'member': member.name,
                        'member_id': member.member_id,
                        'team': team_name,
                        'team_id': member.team_id,
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
        members = Member.query.filter_by(
            room_id=room.room_id,
            name=query_member
        ).all()

        if len(members) == 0:
            return jsonify({
                'success': False,
                'data': {
                    'member': query_member,
                    'exists': False
                }
            }), 404
        elif len(members) == 1:
            # 동명이인 없음
            member = members[0]
            team_name = None
            if member.team_id:
                team = Team.query.filter_by(team_id=member.team_id).first()
                if team:
                    team_name = team.name

            return jsonify({
                'success': True,
                'data': {
                    'member': query_member,
                    'member_id': member.member_id,
                    'team': team_name,
                    'team_id': member.team_id,
                    'exists': True,
                    'is_unique': True
                }
            }), 200
        else:
            # 동명이인 있음
            duplicates = []
            for member in members:
                team_name = None
                if member.team_id:
                    team = Team.query.filter_by(team_id=member.team_id).first()
                    if team:
                        team_name = team.name

                duplicates.append({
                    'member_id': member.member_id,
                    'team': team_name,
                    'team_id': member.team_id
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

    except Exception as e:
        print(f"[MEMBER GET] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['POST'])
@require_admin
def member_post_command():
    data = request.get_json()
    print(f"[MEMBER POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'message': f'Room not found: {request_room}'
            }), 404

        # 동명이인 허용 - 중복 확인 없이 무조건 새로 생성
        member_id = generate_member_id()

        new_member = Member(
            member_id=member_id,
            room_id=room.room_id,
            name=request_member,
            team_id=None
        )
        db.session.add(new_member)
        db.session.commit()

        print(f"[MEMBER POST] Created member: {member_id} ({request_member})")

        return jsonify({
            'success': True,
            'data': {
                'member': request_member,
                'member_id': member_id,
                'team_id': None,
                'created': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[MEMBER POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['DELETE'])
@require_admin
def member_delete_command():
    data = request.get_json()
    print(f"[MEMBER DELETE] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')
    request_member_id = data.get('member_id')

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'message': f'Room not found: {request_room}'
            }), 404

        # member_id가 제공된 경우
        if request_member_id:
            member = Member.query.filter_by(
                member_id=request_member_id,
                room_id=room.room_id
            ).first()

            if member:
                db.session.delete(member)
                db.session.commit()

                return jsonify({
                    'success': True,
                    'data': {
                        'member': member.name,
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
        members = Member.query.filter_by(
            room_id=room.room_id,
            name=request_member
        ).all()

        if len(members) == 0:
            return jsonify({
                'success': False,
                'message': '멤버를 찾을 수 없습니다.',
                'data': {
                    'member': request_member,
                    'exists': False
                }
            }), 404
        elif len(members) > 1:
            # 동명이인 있음
            duplicates = []
            for member in members:
                team_name = None
                if member.team_id:
                    team = Team.query.filter_by(team_id=member.team_id).first()
                    if team:
                        team_name = team.name

                duplicates.append({
                    'member_id': member.member_id,
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
        member = members[0]
        db.session.delete(member)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'member': request_member,
                'member_id': member.member_id,
                'deleted': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
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
    query_room = request.args.get('room')
    if not query_room:
        return jsonify({
            'success': False,
            'message': 'room parameter is required'
        }), 400

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=query_room).first()
        if not room:
            return jsonify({
                'success': True,
                'data': {
                    'room': query_room,
                    'members': [],
                    'count': 0
                }
            }), 200

        # 해당 방의 모든 멤버 조회
        members = Member.query.filter_by(room_id=room.room_id).all()

        members_data = []
        for member in members:
            team_name = None
            if member.team_id:
                team = Team.query.filter_by(team_id=member.team_id).first()
                if team:
                    team_name = team.name

            members_data.append({
                'name': member.name,
                'member_id': member.member_id,
                'room': query_room,
                'team': team_name,
                'team_id': member.team_id
            })

        print(f"[MEMBER LIST] Found {len(members_data)} members in room '{query_room}'")

        return jsonify({
            'success': True,
            'data': {
                'room': query_room,
                'members': members_data,
                'count': len(members_data)
            }
        }), 200

    except Exception as e:
        print(f"[MEMBER LIST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
