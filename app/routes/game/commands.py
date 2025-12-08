"""
경기 관리 API 엔드포인트
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from app.models import db, Game, Lineup, Quarter
from app import socketio
import uuid

bp = Blueprint('game', __name__, url_prefix='/api/game')


def generate_game_id():
    """8자리 고유 게임 ID 생성"""
    return str(uuid.uuid4())[:8].upper()


def emit_game_update(game_id, event_type, data):
    """WebSocket으로 게임 업데이트 브로드캐스트"""
    socketio.emit('game_update', {
        'game_id': game_id,
        'type': event_type,
        'data': data
    }, room=game_id)


def calculate_rotation(game_id, quarter_number):
    """
    쿼터 로테이션 계산 (공통 로직)
    Returns: (playing_blue, bench_blue, playing_white, bench_white, lineups_dict) or (None, error_message)
    """
    # 라인업 가져오기
    blue_lineups = Lineup.query.filter_by(
        game_id=game_id,
        team='블루',
        arrived=True
    ).order_by(Lineup.number).all()

    white_lineups = Lineup.query.filter_by(
        game_id=game_id,
        team='화이트',
        arrived=True
    ).order_by(Lineup.number).all()

    if len(blue_lineups) < 5 or len(white_lineups) < 5:
        return None, 'Each team needs at least 5 players'

    # 이전 쿼터 정보 (로테이션 로직용)
    prev_quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number - 1
    ).first()

    if prev_quarter and quarter_number > 1:
        # 로테이션 로직: 이전 쿼터 벤치 선수들이 먼저 출전
        # 벤치 순서 그대로 코트에 투입 (정순)
        prev_bench_blue = prev_quarter.bench_blue or []
        prev_playing_blue = prev_quarter.playing_blue or []

        # 벤치 정순 + 이전 출전 선수
        rotation_blue = prev_bench_blue + prev_playing_blue
        playing_blue = rotation_blue[:5]
        bench_blue = rotation_blue[5:]

        prev_bench_white = prev_quarter.bench_white or []
        prev_playing_white = prev_quarter.playing_white or []

        rotation_white = prev_bench_white + prev_playing_white
        playing_white = rotation_white[:5]
        bench_white = rotation_white[5:]
    else:
        # 첫 쿼터: 순번대로 1-5번 출전, 나머지 벤치
        playing_blue = [l.number for l in blue_lineups[:5]]
        bench_blue = [l.number for l in blue_lineups[5:]]

        playing_white = [l.number for l in white_lineups[:5]]
        bench_white = [l.number for l in white_lineups[5:]]

    # 라인업 정보 딕셔너리 생성 (번호 -> 이름 매핑)
    lineups_dict = {
        '블루': {l.number: l.member for l in blue_lineups},
        '화이트': {l.number: l.member for l in white_lineups}
    }

    return (playing_blue, bench_blue, playing_white, bench_white, lineups_dict), None


def get_frontend_url():
    """프론트엔드 URL 가져오기 (https:// 자동 추가)"""
    frontend_url = current_app.config['FRONTEND_URL']

    # https:// 또는 http://가 없으면 https:// 추가
    if not frontend_url.startswith('http://') and not frontend_url.startswith('https://'):
        frontend_url = 'https://' + frontend_url

    # 마지막 슬래시 제거
    frontend_url = frontend_url.rstrip('/')

    return frontend_url


@bp.route('/create', methods=['POST'])
def create_game():
    """
    경기 생성
    Body: {
        "room": "카카오톡 방 이름",
        "creator": "생성자 이름",
        "date": "2024-01-25" (optional, 기본값: 오늘)
    }
    """
    data = request.get_json()
    room = data.get('room')
    creator = data.get('creator')
    game_date = data.get('date')

    if not room:
        return jsonify({'success': False, 'error': 'room is required'}), 400

    # 날짜 파싱 (기본값: 오늘)
    if game_date:
        try:
            game_date = datetime.strptime(game_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format (use YYYY-MM-DD)'}), 400
    else:
        game_date = date.today()

    # 게임 ID 생성 (충돌 방지)
    game_id = generate_game_id()
    while Game.query.filter_by(game_id=game_id).first():
        game_id = generate_game_id()

    # 게임 생성
    game = Game(
        game_id=game_id,
        room=room,
        creator=creator,
        date=game_date,
        status='준비중',
        current_quarter=0
    )

    try:
        db.session.add(game)
        db.session.commit()

        # 게임 URL 생성 (환경 변수에서 프론트엔드 URL 가져오기)
        frontend_url = get_frontend_url()
        game_url = f"{frontend_url}/game/{game_id}"

        return jsonify({
            'success': True,
            'data': {
                'game_id': game_id,
                'url': game_url,
                'game': game.to_dict()
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/all', methods=['GET'])
def get_all_games():
    """
    모든 경기 목록 조회 (페이지네이션)
    Query Parameters:
        - page: 페이지 번호 (기본값: 1)
        - limit: 페이지당 항목 수 (기본값: 10, 최대: 100)
        - room: 특정 방의 경기만 필터링 (선택사항)
        - days: 최근 N일 이내 경기만 필터링 (선택사항, 예: 7)
    """
    try:
        # 쿼리 파라미터 파싱
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        room = request.args.get('room', None)
        days = request.args.get('days', None, type=int)

        # 유효성 검사
        if page < 1:
            page = 1
        if limit < 1:
            limit = 10
        if limit > 100:
            limit = 100

        # 기본 쿼리
        query = Game.query

        # room 필터링 (선택사항)
        if room:
            query = query.filter(Game.room == room)

        # days 필터링 (선택사항)
        if days and days > 0:
            from datetime import timedelta
            cutoff_date = date.today() - timedelta(days=days)
            query = query.filter(Game.date >= cutoff_date)

        # 최신순 정렬
        query = query.order_by(Game.created_at.desc())

        # 페이지네이션
        pagination = query.paginate(
            page=page,
            per_page=limit,
            error_out=False
        )

        # 프론트엔드 URL
        frontend_url = get_frontend_url()

        # 경기 데이터 변환
        games_data = []
        for game in pagination.items:
            games_data.append({
                'game_id': game.game_id,
                'url': f"{frontend_url}/game/{game.game_id}",
                'room': game.room,
                'creator': game.creator,
                'date': game.date.isoformat() if game.date else None,
                'created_at': game.created_at.isoformat() if game.created_at else None,
                'status': game.status,
                'current_quarter': game.current_quarter,
                'winner': game.winner,
                'final_score_blue': game.final_score_blue,
                'final_score_white': game.final_score_white
            })

        return jsonify({
            'success': True,
            'data': {
                'games': games_data,
                'pagination': {
                    'page': pagination.page,
                    'limit': limit,
                    'total_items': pagination.total,
                    'total_pages': pagination.pages,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/rooms', methods=['GET'])
def get_rooms():
    """
    모든 방 목록 조회 (중복 제거)
    경기가 등록된 방들의 목록을 반환합니다.
    """
    try:
        # 모든 방 이름을 중복 없이 조회 (room이 NULL이 아닌 경우만)
        rooms = db.session.query(Game.room).filter(
            Game.room.isnot(None),
            Game.room != ''
        ).distinct().order_by(Game.room).all()

        # 튜플을 문자열 리스트로 변환
        room_list = [room[0] for room in rooms]

        return jsonify({
            'success': True,
            'data': {
                'rooms': room_list,
                'count': len(room_list)
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>', methods=['GET'])
def get_game(game_id):
    """
    경기 조회
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    # 라인업 조회
    lineups = Lineup.query.filter_by(game_id=game_id).order_by(Lineup.team, Lineup.number).all()
    lineups_data = {
        '블루': [l.to_dict() for l in lineups if l.team == '블루'],
        '화이트': [l.to_dict() for l in lineups if l.team == '화이트']
    }

    # 쿼터 조회
    quarters = Quarter.query.filter_by(game_id=game_id).order_by(Quarter.quarter_number).all()
    quarters_data = [q.to_dict() for q in quarters]

    return jsonify({
        'success': True,
        'data': {
            'game': game.to_dict(),
            'lineups': lineups_data,
            'quarters': quarters_data
        }
    }), 200


@bp.route('/<game_id>/start', methods=['POST'])
def start_game(game_id):
    """
    경기 시작
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    if game.status != '준비중':
        return jsonify({'success': False, 'error': f'Game is already {game.status}'}), 400

    try:
        game.status = '진행중'
        game.started_at = datetime.utcnow()
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'game_started', game.to_dict())

        return jsonify({
            'success': True,
            'data': game.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/end', methods=['POST'])
def end_game(game_id):
    """
    경기 종료
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    if game.status == '종료':
        return jsonify({'success': False, 'error': 'Game already ended'}), 400

    try:
        # 모든 쿼터의 점수 합산
        quarters = Quarter.query.filter_by(game_id=game_id).all()
        total_blue = sum(q.score_blue for q in quarters)
        total_white = sum(q.score_white for q in quarters)

        # 승자 결정
        if total_blue > total_white:
            winner = '블루'
        elif total_white > total_blue:
            winner = '화이트'
        else:
            winner = '무승부'

        game.status = '종료'
        game.ended_at = datetime.utcnow()
        game.final_score_blue = total_blue
        game.final_score_white = total_white
        game.winner = winner

        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'game_ended', game.to_dict())

        return jsonify({
            'success': True,
            'data': game.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>', methods=['DELETE'])
def delete_game(game_id):
    """
    경기 삭제 (CASCADE로 연관 데이터 모두 삭제)
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    try:
        db.session.delete(game)
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'game_deleted', {'game_id': game_id})

        return jsonify({
            'success': True,
            'message': 'Game deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/lineup/arrival', methods=['POST'])
def player_arrival(game_id):
    """
    선수 도착 처리
    Body: {
        "team": "블루" or "화이트",
        "member": "선수 이름"
    }
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    data = request.get_json()
    team = data.get('team')
    member = data.get('member')

    if team not in ['블루', '화이트']:
        return jsonify({'success': False, 'error': 'team must be "블루" or "화이트"'}), 400

    if not member:
        return jsonify({'success': False, 'error': 'member is required'}), 400

    try:
        # 해당 팀의 다음 번호 계산
        last_lineup = Lineup.query.filter_by(
            game_id=game_id,
            team=team
        ).order_by(Lineup.number.desc()).first()

        next_number = (last_lineup.number + 1) if last_lineup else 1

        # 라인업 추가
        lineup = Lineup(
            game_id=game_id,
            team=team,
            member=member,
            number=next_number,
            arrived=True,
            arrived_at=datetime.utcnow()
        )

        db.session.add(lineup)
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'player_arrived', {
            'lineup': lineup.to_dict()
        })

        return jsonify({
            'success': True,
            'data': lineup.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/lineup/<int:lineup_id>', methods=['DELETE'])
def remove_player(game_id, lineup_id):
    """
    선수 제거
    """
    lineup = Lineup.query.filter_by(id=lineup_id, game_id=game_id).first()

    if not lineup:
        return jsonify({'success': False, 'error': 'Lineup not found'}), 404

    try:
        team = lineup.team
        number = lineup.number

        db.session.delete(lineup)

        # 뒤의 번호들 재정렬
        later_lineups = Lineup.query.filter(
            Lineup.game_id == game_id,
            Lineup.team == team,
            Lineup.number > number
        ).all()

        for l in later_lineups:
            l.number -= 1

        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'player_removed', {
            'lineup_id': lineup_id,
            'team': team
        })

        return jsonify({
            'success': True,
            'message': 'Player removed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/preview', methods=['GET'])
def preview_quarter(game_id):
    """
    쿼터 미리보기 - 자동 로테이션 결과만 계산해서 반환 (Quarter 생성하지 않음)
    Query: ?quarter_number=2 (optional, 기본값: 현재 쿼터 + 1)
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    if game.status != '진행중':
        return jsonify({'success': False, 'error': 'Game must be started first'}), 400

    quarter_number = request.args.get('quarter_number', game.current_quarter + 1, type=int)

    # 이미 존재하는 쿼터인지 확인
    existing_quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if existing_quarter:
        return jsonify({'success': False, 'error': f'Quarter {quarter_number} already exists'}), 400

    try:
        # 로테이션 계산
        result, error = calculate_rotation(game_id, quarter_number)

        if error:
            return jsonify({'success': False, 'error': error}), 400

        playing_blue, bench_blue, playing_white, bench_white, lineups_dict = result

        return jsonify({
            'success': True,
            'data': {
                'quarter_number': quarter_number,
                'playing_blue': playing_blue,
                'bench_blue': bench_blue,
                'playing_white': playing_white,
                'bench_white': bench_white,
                'lineups': lineups_dict
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/start', methods=['POST'])
def start_quarter(game_id):
    """
    쿼터 시작
    Body: {
        "quarter_number": 1 (optional, 기본값: 현재 쿼터 + 1),
        "playing_blue": [1,2,3,4,5] (optional, 없으면 자동 로테이션),
        "bench_blue": [6,7,8] (optional),
        "playing_white": [1,2,3,4,5] (optional),
        "bench_white": [6,7,8] (optional)
    }
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    if game.status != '진행중':
        return jsonify({'success': False, 'error': 'Game must be started first'}), 400

    data = request.get_json() or {}
    quarter_number = data.get('quarter_number', game.current_quarter + 1)

    # 이미 존재하는 쿼터인지 확인
    existing_quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if existing_quarter:
        return jsonify({'success': False, 'error': f'Quarter {quarter_number} already exists'}), 400

    try:
        # Body에 명단이 있으면 사용, 없으면 자동 로테이션
        if 'playing_blue' in data and 'playing_white' in data:
            playing_blue = data.get('playing_blue', [])
            bench_blue = data.get('bench_blue', [])
            playing_white = data.get('playing_white', [])
            bench_white = data.get('bench_white', [])

            # 유효성 검사
            if len(playing_blue) != 5 or len(playing_white) != 5:
                return jsonify({
                    'success': False,
                    'error': 'Each team must have exactly 5 playing players'
                }), 400
        else:
            # 자동 로테이션
            result, error = calculate_rotation(game_id, quarter_number)

            if error:
                return jsonify({'success': False, 'error': error}), 400

            playing_blue, bench_blue, playing_white, bench_white, _ = result

        # 쿼터 생성
        quarter = Quarter(
            game_id=game_id,
            quarter_number=quarter_number,
            status='진행중',
            playing_blue=playing_blue,
            playing_white=playing_white,
            bench_blue=bench_blue,
            bench_white=bench_white,
            score_blue=0,
            score_white=0,
            started_at=datetime.utcnow()
        )

        db.session.add(quarter)
        game.current_quarter = quarter_number
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'quarter_started', quarter.to_dict())

        return jsonify({
            'success': True,
            'data': quarter.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/<int:quarter_number>/end', methods=['POST'])
def end_quarter(game_id, quarter_number):
    """
    쿼터 종료
    """
    quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if not quarter:
        return jsonify({'success': False, 'error': 'Quarter not found'}), 404

    if quarter.status == '종료':
        return jsonify({'success': False, 'error': 'Quarter already ended'}), 400

    try:
        quarter.status = '종료'
        quarter.ended_at = datetime.utcnow()
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'quarter_ended', quarter.to_dict())

        return jsonify({
            'success': True,
            'data': quarter.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/<int:quarter_number>/score', methods=['PUT'])
def update_score(game_id, quarter_number):
    """
    쿼터 점수 업데이트
    Body: {
        "score_blue": 10,
        "score_white": 8
    }
    """
    quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if not quarter:
        return jsonify({'success': False, 'error': 'Quarter not found'}), 404

    data = request.get_json()
    score_blue = data.get('score_blue')
    score_white = data.get('score_white')

    if score_blue is None or score_white is None:
        return jsonify({'success': False, 'error': 'Both score_blue and score_white are required'}), 400

    try:
        quarter.score_blue = score_blue
        quarter.score_white = score_white
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'score_updated', {
            'quarter': quarter_number,
            'score_blue': score_blue,
            'score_white': score_white
        })

        return jsonify({
            'success': True,
            'data': quarter.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
