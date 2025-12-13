"""
방 관리 API
"""
import uuid
from flask import Blueprint, jsonify, request
from app.models import db, Room, Game

bp = Blueprint('room', __name__, url_prefix='/api/room')


def generate_room_id():
    """8자리 고유 방 ID 생성 (게임 ID와 동일한 방식)"""
    return str(uuid.uuid4())[:8].upper()


@bp.route('/<room_id>', methods=['GET'])
def get_room(room_id):
    """
    방 정보 조회
    """
    room = Room.query.filter_by(room_id=room_id).first()

    if not room:
        return jsonify({'success': False, 'error': 'Room not found'}), 404

    # 해당 방의 경기 목록 조회
    games = Game.query.filter_by(room_id=room_id).order_by(Game.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'room': room.to_dict(),
            'games_count': len(games)
        }
    }), 200


@bp.route('/<room_id>/games', methods=['GET'])
def get_room_games(room_id):
    """
    방의 경기 목록 조회 (페이지네이션)
    """
    room = Room.query.filter_by(room_id=room_id).first()

    if not room:
        return jsonify({'success': False, 'error': 'Room not found'}), 404

    # 페이지네이션 파라미터
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    # 경기 목록 조회
    pagination = Game.query.filter_by(room_id=room_id)\
        .order_by(Game.created_at.desc())\
        .paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'success': True,
        'data': {
            'room': room.to_dict(),
            'games': [game.to_dict() for game in pagination.items],
            'pagination': {
                'page': page,
                'limit': limit,
                'total_items': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }
    }), 200


@bp.route('/by-name/<room_name>', methods=['GET'])
def get_room_by_name(room_name):
    """
    방 이름으로 room_id 조회
    """
    room = Room.query.filter_by(name=room_name).first()

    if not room:
        return jsonify({'success': False, 'error': 'Room not found'}), 404

    return jsonify({
        'success': True,
        'data': room.to_dict()
    }), 200


@bp.route('/create', methods=['POST'])
def create_room():
    """
    새 방 생성 (카톡봇에서 호출)
    Body: {
        "name": "방 이름"
    }
    """
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'success': False, 'error': 'name is required'}), 400

    # 중복 이름 체크
    existing = Room.query.filter_by(name=name).first()
    if existing:
        return jsonify({
            'success': False,
            'error': f'Room with name "{name}" already exists',
            'data': existing.to_dict()
        }), 409

    try:
        # room_id 생성 (중복 체크)
        room_id = generate_room_id()
        while Room.query.filter_by(room_id=room_id).first():
            room_id = generate_room_id()

        # 방 생성
        room = Room(
            room_id=room_id,
            name=name
        )

        db.session.add(room)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': room.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/list', methods=['GET'])
def list_rooms():
    """
    모든 방 목록 조회
    """
    rooms = Room.query.order_by(Room.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': {
            'rooms': [room.to_dict() for room in rooms]
        }
    }), 200
