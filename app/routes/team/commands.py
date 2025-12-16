from flask import Blueprint, request, jsonify
from app.models import db, Room, Team, Member
from app.utils import generate_team_id
from app.routes.admin.auth import require_admin
from datetime import datetime

bp = Blueprint('team_commands', __name__, url_prefix='/api/commands/team')

@bp.route('/', methods=['GET'])
def team_get_command():
    # GET 요청: 쿼리 스트링에서 파라미터 읽기
    query_room = request.args.get('room', 'unknown')
    query_team = request.args.get('team', 'unknown')

    print(f"[TEAM GET] Query params: room={query_room}, team={query_team}")

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=query_room).first()
        if not room:
            return jsonify({
                'success': False,
                'data': {
                    'team': query_team,
                    'exists': False
                }
            }), 404

        # 팀 조회
        team = Team.query.filter_by(
            room_id=room.room_id,
            name=query_team
        ).first()

        if team:
            # 팀에 속한 멤버들 조회
            members = Member.query.filter_by(
                room_id=room.room_id,
                team_id=team.team_id
            ).all()

            members_data = []
            for member in members:
                members_data.append({
                    'name': member.name,
                    'member_id': member.member_id
                })

            return jsonify({
                'success': True,
                'data': {
                    'team': query_team,
                    'team_id': team.team_id,
                    'member_count': len(members_data),
                    'members': members_data,
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
    data = request.get_json()
    print(f"[TEAM POST] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_team = data.get('team', 'unknown')

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'message': f'Room not found: {request_room}'
            }), 404

        # 중복 체크
        existing_team = Team.query.filter_by(
            room_id=room.room_id,
            name=request_team
        ).first()

        if existing_team:
            return jsonify({
                'success': False,
                'data': {
                    'team': request_team,
                    'team_id': existing_team.team_id,
                    'created': False,
                    'reason': 'already_exists'
                }
            }), 409

        # 새 팀 생성
        team_id = generate_team_id()
        new_team = Team(
            team_id=team_id,
            room_id=room.room_id,
            name=request_team
        )
        db.session.add(new_team)
        db.session.commit()

        print(f"[TEAM POST] Created team: {team_id} ({request_team})")

        return jsonify({
            'success': True,
            'data': {
                'team': request_team,
                'team_id': team_id,
                'created': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[TEAM POST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500


@bp.route('/', methods=['DELETE'])
@require_admin
def team_delete_command():
    data = request.get_json()
    print(f"[TEAM DELETE] Received JSON: {data}")

    request_room = data.get('room', 'unknown')
    request_team = data.get('team', 'unknown')

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=request_room).first()
        if not room:
            return jsonify({
                'success': False,
                'data': {
                    'team': request_team,
                    'deleted': False,
                    'reason': 'room_not_found'
                }
            }), 404

        # 팀 조회
        team = Team.query.filter_by(
            room_id=room.room_id,
            name=request_team
        ).first()

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
        member_count = Member.query.filter_by(
            room_id=room.room_id,
            team_id=team.team_id
        ).count()

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
        db.session.delete(team)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'team': request_team,
                'team_id': team.team_id,
                'deleted': True
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[TEAM DELETE] Error: {e}")
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
                    'teams': [],
                    'count': 0
                }
            }), 200

        # 해당 방의 모든 팀 조회
        teams = Team.query.filter_by(room_id=room.room_id).all()

        teams_data = []
        for team in teams:
            # 팀 멤버 수 계산
            member_count = Member.query.filter_by(
                room_id=room.room_id,
                team_id=team.team_id
            ).count()

            teams_data.append({
                'name': team.name,
                'team_id': team.team_id,
                'room': query_room,
                'member_count': member_count
            })

        print(f"[TEAM LIST] Found {len(teams_data)} teams in room '{query_room}'")

        return jsonify({
            'success': True,
            'data': {
                'room': query_room,
                'teams': teams_data,
                'count': len(teams_data)
            }
        }), 200

    except Exception as e:
        print(f"[TEAM LIST] Error: {e}")
        return jsonify({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        }), 500
