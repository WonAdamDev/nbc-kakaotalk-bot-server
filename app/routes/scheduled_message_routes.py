"""
예약 메시지 관리 API
"""
from flask import Blueprint, request, jsonify
from app.models import db, ScheduledMessage, Room
from app.routes.admin.auth import require_admin
from datetime import datetime, time

bp = Blueprint('scheduled_messages', __name__, url_prefix='/api/scheduled-messages')


@bp.route('', methods=['GET'])
def get_scheduled_messages():
    """
    예약 메시지 목록 조회 (관리자용)
    Query: room={room_name}
    """
    room_name = request.args.get('room')
    if not room_name:
        return jsonify({'success': False, 'error': 'room parameter required'}), 400

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=room_name).first()
        if not room:
            return jsonify({
                'success': True,
                'data': {'scheduled_messages': [], 'count': 0}
            }), 200

        # 예약 메시지 조회
        messages = ScheduledMessage.query.filter_by(
            room_id=room.room_id
        ).order_by(
            ScheduledMessage.scheduled_time,
            ScheduledMessage.created_at.desc()
        ).all()

        messages_data = [msg.to_dict() for msg in messages]

        return jsonify({
            'success': True,
            'data': {
                'scheduled_messages': messages_data,
                'count': len(messages_data)
            }
        }), 200

    except Exception as e:
        print(f"[GET /scheduled-messages] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('', methods=['POST'])
@require_admin
def create_scheduled_message():
    """
    예약 메시지 생성
    Body: {
        room: "방이름",
        message: "메시지 내용",
        scheduled_time: "09:00",
        days_of_week: [1, 2, 3, 4, 5],  // 1=월요일, 7=일요일
        created_by: "관리자"
    }
    """
    data = request.get_json()
    room_name = data.get('room')
    message = data.get('message')
    scheduled_time_str = data.get('scheduled_time')
    days_of_week = data.get('days_of_week', [])
    created_by = data.get('created_by', 'Admin')

    # 유효성 검사
    if not room_name or not message or not scheduled_time_str:
        return jsonify({
            'success': False,
            'error': 'room, message, and scheduled_time are required'
        }), 400

    if not days_of_week or not isinstance(days_of_week, list):
        return jsonify({
            'success': False,
            'error': 'days_of_week must be a non-empty array'
        }), 400

    # 요일 검증 (1-7)
    if not all(1 <= day <= 7 for day in days_of_week):
        return jsonify({
            'success': False,
            'error': 'days_of_week must contain values between 1 (Monday) and 7 (Sunday)'
        }), 400

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=room_name).first()
        if not room:
            return jsonify({'success': False, 'error': f'Room not found: {room_name}'}), 404

        # 시간 파싱 (HH:MM)
        try:
            hour, minute = map(int, scheduled_time_str.split(':'))
            scheduled_time = time(hour, minute)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid time format. Use HH:MM (e.g., 09:00)'
            }), 400

        # 예약 메시지 생성
        new_message = ScheduledMessage(
            room_id=room.room_id,
            message=message,
            scheduled_time=scheduled_time,
            days_of_week=days_of_week,
            is_active=True,
            created_by=created_by
        )

        db.session.add(new_message)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': new_message.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[POST /scheduled-message] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:message_id>', methods=['PUT'])
@require_admin
def update_scheduled_message(message_id):
    """
    예약 메시지 수정
    Body: {
        message: "수정된 메시지",
        scheduled_time: "10:00",
        days_of_week: [1, 3, 5],
        is_active: true
    }
    """
    data = request.get_json()

    try:
        # 예약 메시지 조회
        scheduled_msg = ScheduledMessage.query.get(message_id)
        if not scheduled_msg:
            return jsonify({'success': False, 'error': 'Scheduled message not found'}), 404

        # 필드 업데이트
        if 'message' in data:
            scheduled_msg.message = data['message']

        if 'scheduled_time' in data:
            try:
                hour, minute = map(int, data['scheduled_time'].split(':'))
                scheduled_msg.scheduled_time = time(hour, minute)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid time format. Use HH:MM'
                }), 400

        if 'days_of_week' in data:
            days = data['days_of_week']
            if not isinstance(days, list) or not all(1 <= day <= 7 for day in days):
                return jsonify({
                    'success': False,
                    'error': 'Invalid days_of_week'
                }), 400
            scheduled_msg.days_of_week = days

        if 'is_active' in data:
            scheduled_msg.is_active = bool(data['is_active'])

        db.session.commit()

        return jsonify({
            'success': True,
            'data': scheduled_msg.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[PUT /scheduled-message/{message_id}] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:message_id>', methods=['DELETE'])
@require_admin
def delete_scheduled_message(message_id):
    """
    예약 메시지 삭제
    """
    try:
        scheduled_msg = ScheduledMessage.query.get(message_id)
        if not scheduled_msg:
            return jsonify({'success': False, 'error': 'Scheduled message not found'}), 404

        db.session.delete(scheduled_msg)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        print(f"[DELETE /scheduled-message/{message_id}] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/pending', methods=['GET'])
def get_pending_messages():
    """
    봇이 전송할 예약 메시지 조회
    Query: room={room_name}, current_time={HH:MM}, current_day={1-7}

    현재 시각과 요일에 해당하는 활성화된 예약 메시지를 반환합니다.
    """
    room_name = request.args.get('room')
    current_time_str = request.args.get('current_time')
    current_day_str = request.args.get('current_day')

    if not room_name:
        return jsonify({'success': False, 'error': 'room parameter required'}), 400

    try:
        # room_id 가져오기
        room = Room.query.filter_by(name=room_name).first()
        if not room:
            return jsonify({
                'success': True,
                'data': {'pending_messages': []}
            }), 200

        # 현재 시각과 요일 (제공되지 않으면 서버 시각 사용)
        if current_time_str:
            try:
                hour, minute = map(int, current_time_str.split(':'))
                current_time = time(hour, minute)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid time format'}), 400
        else:
            now = datetime.now()
            current_time = now.time()

        if current_day_str:
            current_day = int(current_day_str)
            if not 1 <= current_day <= 7:
                return jsonify({'success': False, 'error': 'current_day must be 1-7'}), 400
        else:
            # Python weekday(): 0=월요일, 6=일요일 -> 1=월요일, 7=일요일로 변환
            current_day = datetime.now().weekday() + 1

        # 해당 시각과 요일에 맞는 예약 메시지 조회
        messages = ScheduledMessage.query.filter(
            ScheduledMessage.room_id == room.room_id,
            ScheduledMessage.is_active == True,
            ScheduledMessage.scheduled_time == current_time
        ).all()

        # 오늘 요일이 포함된 메시지만 필터링
        pending_messages = [
            msg.to_dict() for msg in messages
            if current_day in msg.days_of_week
        ]

        return jsonify({
            'success': True,
            'data': {
                'pending_messages': pending_messages,
                'current_time': current_time.strftime('%H:%M'),
                'current_day': current_day
            }
        }), 200

    except Exception as e:
        print(f"[GET /scheduled-message/pending] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
