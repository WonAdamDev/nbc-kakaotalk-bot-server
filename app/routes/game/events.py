"""
WebSocket 이벤트 핸들러
"""
from app import socketio
from flask_socketio import emit, join_room, leave_room


@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    print(f'[WebSocket] Client connected')
    emit('connected', {'message': 'Connected to game server'})


@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print(f'[WebSocket] Client disconnected')


@socketio.on('join_game')
def handle_join_game(data):
    """
    경기 방에 참여
    data: {"game_id": "ABC12345"}
    """
    game_id = data.get('game_id')
    if game_id:
        join_room(game_id)
        print(f'[WebSocket] Client joined game room: {game_id}')
        emit('joined_game', {
            'game_id': game_id,
            'message': f'Joined game {game_id}'
        }, room=game_id)


@socketio.on('leave_game')
def handle_leave_game(data):
    """
    경기 방 나가기
    data: {"game_id": "ABC12345"}
    """
    game_id = data.get('game_id')
    if game_id:
        leave_room(game_id)
        print(f'[WebSocket] Client left game room: {game_id}')
        emit('left_game', {
            'game_id': game_id,
            'message': f'Left game {game_id}'
        })


@socketio.on('request_game_state')
def handle_request_game_state(data):
    """
    현재 경기 상태 요청
    data: {"game_id": "ABC12345"}
    """
    game_id = data.get('game_id')
    if not game_id:
        emit('error', {'message': 'game_id is required'})
        return

    from app.models import Game, Lineup, Quarter

    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        emit('error', {'message': 'Game not found'})
        return

    # 라인업 조회
    lineups = Lineup.query.filter_by(game_id=game_id).order_by(Lineup.team, Lineup.number).all()
    lineups_data = {
        '블루': [l.to_dict() for l in lineups if l.team == '블루'],
        '화이트': [l.to_dict() for l in lineups if l.team == '화이트']
    }

    # 쿼터 조회
    quarters = Quarter.query.filter_by(game_id=game_id).order_by(Quarter.quarter_number).all()
    quarters_data = [q.to_dict() for q in quarters]

    # 현재 상태 전송
    emit('game_state', {
        'game': game.to_dict(),
        'lineups': lineups_data,
        'quarters': quarters_data
    })
