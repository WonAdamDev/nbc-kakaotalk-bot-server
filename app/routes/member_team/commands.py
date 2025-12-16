from flask import Blueprint, request, jsonify
from app.models import db, Room, Member, Team
from app.routes.admin.auth import require_admin

bp = Blueprint('member_team_commands', __name__, url_prefix='/api/commands/member_team')

@bp.route('/', methods=['GET'])
def member_team_get_command():
    """멤버의 팀 배정 조회"""
    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    request_room = request.args.get('room', 'unknown')
    request_member = request.args.get('member', 'unknown')
    request_member_id = request.args.get('member_id')

    print(f"[MEMBER_TEAM GET] Query params: room={request_room}, member={request_member}, member_id={request_member_id}")

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'data': {
                    'member': request_member,
                    'is_member': False
                }
            }), 404

        # member_id가 제공된 경우 ID로 직접 조회
        if request_member_id:
            member = Member.query.filter_by(
                member_id=request_member_id,
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
                        'is_member': True,
                        'is_unique': True
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'is_member': False
                    }
                }), 404

        # 이름으로 조회 (동명이인 체크)
        members = Member.query.filter_by(
            room_id=room.room_id,
            name=request_member
        ).all()

        if len(members) == 0:
            return jsonify({
                'success': False,
                'data': {
                    'member': request_member,
                    'is_member': False
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
                    'member': request_member,
                    'member_id': member.member_id,
                    'team': team_name,
                    'is_member': True,
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
                    'team': team_name
                })

            return jsonify({
                'success': True,
                'data': {
                    'member': request_member,
                    'is_member': True,
                    'is_unique': False,
                    'duplicates': duplicates,
                    'count': len(duplicates)
                }
            }), 200

    except Exception as e:
        print(f"[MEMBER_TEAM GET] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['POST'])
@require_admin
def member_team_post_command():
    """멤버를 팀에 배정"""
    data = request.get_json()
    print(f"[MEMBER_TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_member = data.get('member', 'unknown')
    request_team = data.get('team')
    request_member_id = data.get('member_id')

    if not request_team:
        return jsonify({
            'success': False,
            'message': '팀 이름을 입력해주세요.'
        }), 400

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'message': f'Room not found: {request_room}'
            }), 404

        # 멤버 조회
        member = None
        if request_member_id:
            member = Member.query.filter_by(
                member_id=request_member_id,
                room_id=room.room_id
            ).first()

            if not member:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'member_id': request_member_id,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404
        else:
            # 이름으로 조회 - 동명이인 체크
            members = Member.query.filter_by(
                room_id=room.room_id,
                name=request_member
            ).all()

            if len(members) == 0:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404
            elif len(members) > 1:
                # 동명이인 있음
                duplicates = []
                for m in members:
                    team_name = None
                    if m.team_id:
                        t = Team.query.filter_by(team_id=m.team_id).first()
                        if t:
                            team_name = t.name

                    duplicates.append({
                        'member_id': m.member_id,
                        'team': team_name
                    })

                return jsonify({
                    'success': False,
                    'message': '동명이인이 존재합니다. member_id를 지정해주세요.',
                    'data': {
                        'member': request_member,
                        'team': request_team,
                        'assigned': False,
                        'reason': 'duplicate_members',
                        'duplicates': duplicates,
                        'count': len(duplicates)
                    }
                }), 409

            member = members[0]

        # 팀 존재 확인
        team = Team.query.filter_by(
            room_id=room.room_id,
            name=request_team
        ).first()

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

        # 멤버의 team_id 업데이트
        member.team_id = team.team_id
        db.session.commit()

        print(f"[MEMBER_TEAM POST] Assigned {request_member} to team {request_team} (ID: {team.team_id})")

        return jsonify({
            'success': True,
            'data': {
                'member': member.name,
                'member_id': member.member_id,
                'team': request_team,
                'team_id': team.team_id,
                'assigned': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[MEMBER_TEAM POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500

@bp.route('/', methods=['DELETE'])
@require_admin
def member_team_delete_command():
    """멤버의 팀 배정 해제"""
    data = request.get_json()
    print(f"[MEMBER_TEAM DELETE] Received JSON: {data}")

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

        # 멤버 조회
        member = None
        if request_member_id:
            member = Member.query.filter_by(
                member_id=request_member_id,
                room_id=room.room_id
            ).first()

            if not member:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'member_id': request_member_id,
                        'unassigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404
        else:
            # 이름으로 조회 - 동명이인 체크
            members = Member.query.filter_by(
                room_id=room.room_id,
                name=request_member
            ).all()

            if len(members) == 0:
                return jsonify({
                    'success': False,
                    'data': {
                        'member': request_member,
                        'unassigned': False,
                        'reason': 'member_not_found'
                    }
                }), 404
            elif len(members) > 1:
                # 동명이인 있음
                duplicates = []
                for m in members:
                    team_name = None
                    if m.team_id:
                        t = Team.query.filter_by(team_id=m.team_id).first()
                        if t:
                            team_name = t.name

                    duplicates.append({
                        'member_id': m.member_id,
                        'team': team_name
                    })

                return jsonify({
                    'success': False,
                    'message': '동명이인이 존재합니다. member_id를 지정해주세요.',
                    'data': {
                        'member': request_member,
                        'unassigned': False,
                        'reason': 'duplicate_members',
                        'duplicates': duplicates,
                        'count': len(duplicates)
                    }
                }), 409

            member = members[0]

        # 이전 팀 정보 저장
        previous_team_name = None
        if member.team_id:
            team = Team.query.filter_by(team_id=member.team_id).first()
            if team:
                previous_team_name = team.name

        # 팀 배정 해제
        member.team_id = None
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'member': member.name,
                'member_id': member.member_id,
                'previous_team': previous_team_name,
                'unassigned': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[MEMBER_TEAM DELETE] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
