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
    print(f'[WebSocket] Broadcasting to room {game_id}: {event_type}')
    socketio.emit('game_update', {
        'game_id': game_id,
        'type': event_type,
        'data': data
    }, to=game_id)
    print(f'[WebSocket] Broadcast sent to room {game_id}')


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

        # 디버깅 로그
        print(f"[/api/game/all] Query params - page: {page}, limit: {limit}, room: {room}, days: {days}")

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
    Body (required): {
        "team_home": "1팀",
        "team_away": "2팀"
    }

    주의: 경기 시작 후에는 팀 정보를 변경할 수 없습니다.
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    if game.status != '준비중':
        return jsonify({'success': False, 'error': f'Game is already {game.status}'}), 400

    # 경기 시작 후 팀 정보 변경 방지
    # (현재는 start_game이 '준비중'일 때만 실행되므로 이미 방지되지만,
    #  나중에 게임 업데이트 엔드포인트가 추가될 경우를 대비한 명시적 체크)
    if game.team_home or game.team_away:
        return jsonify({
            'success': False,
            'error': 'Teams are already set. Cannot change teams after they are set.'
        }), 400

    data = request.get_json() or {}
    team_home = data.get('team_home')
    team_away = data.get('team_away')

    # 팀 선택 검증 - 필수
    if not team_home or not team_away:
        return jsonify({
            'success': False,
            'error': 'Both team_home and team_away are required'
        }), 400

    # 두 팀이 같은지 확인
    if team_home == team_away:
        return jsonify({
            'success': False,
            'error': 'team_home and team_away must be different'
        }), 400

    try:
        game.status = '진행중'
        game.started_at = datetime.utcnow()
        game.team_home = team_home
        game.team_away = team_away
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
        # 마지막 쿼터의 누적 점수 (쿼터 번호 순으로 정렬 후 마지막)
        quarters = Quarter.query.filter_by(game_id=game_id).order_by(Quarter.quarter_number.asc()).all()

        if not quarters:
            return jsonify({'success': False, 'error': 'No quarters found'}), 400

        last_quarter = quarters[-1]
        total_blue = last_quarter.score_blue
        total_white = last_quarter.score_white

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
    선수 제거 (조퇴)
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    # 경기가 종료되었으면 제거 불가
    if game.status == '종료':
        return jsonify({'success': False, 'error': 'Cannot remove player after game ended'}), 400

    # 진행중인 쿼터가 있으면 제거 불가
    ongoing_quarter = Quarter.query.filter_by(
        game_id=game_id,
        status='진행중'
    ).first()

    if ongoing_quarter:
        return jsonify({'success': False, 'error': 'Cannot remove player while quarter is ongoing'}), 400

    lineup = Lineup.query.filter_by(id=lineup_id, game_id=game_id).first()

    if not lineup:
        return jsonify({'success': False, 'error': 'Lineup not found'}), 404

    try:
        team = lineup.team
        number = lineup.number
        member_name = lineup.member

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

        # 업데이트된 팀 라인업 조회
        updated_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team=team,
            arrived=True
        ).order_by(Lineup.number).all()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'player_removed', {
            'lineup_id': lineup_id,
            'team': team,
            'lineups': [l.to_dict() for l in updated_lineups]
        })

        return jsonify({
            'success': True,
            'message': 'Player removed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/lineup/swap', methods=['PUT'])
def swap_lineup_numbers(game_id):
    """
    순번 교체 (드래그앤드롭) - 같은 팀 또는 다른 팀 간 교체 지원
    Body: {
        "from_team": "블루",
        "from_number": 5,
        "to_team": "화이트",
        "to_number": 3
    }

    또는 기존 호환성을 위한 형식:
    Body: {
        "team": "블루",
        "from_number": 5,
        "to_number": 3
    }
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    # 경기가 종료되었으면 순번 변경 불가
    if game.status == '종료':
        return jsonify({'success': False, 'error': 'Cannot swap lineup after game ended'}), 400

    # 진행중인 쿼터가 있으면 순번 변경 불가
    ongoing_quarter = Quarter.query.filter_by(
        game_id=game_id,
        status='진행중'
    ).first()

    if ongoing_quarter:
        return jsonify({'success': False, 'error': 'Cannot swap lineup while quarter is ongoing'}), 400

    data = request.get_json()

    # 새 형식 (다른 팀 간 교체 지원)
    from_team = data.get('from_team')
    from_number = data.get('from_number')
    to_team = data.get('to_team')
    to_number = data.get('to_number')

    # 기존 형식 호환 (같은 팀 내 교체)
    if not from_team or not to_team:
        team = data.get('team')
        if team:
            from_team = team
            to_team = team

    if from_team not in ['블루', '화이트'] or to_team not in ['블루', '화이트']:
        return jsonify({'success': False, 'error': 'teams must be "블루" or "화이트"'}), 400

    if not from_number or not to_number:
        return jsonify({'success': False, 'error': 'from_number and to_number are required'}), 400

    if from_team == to_team and from_number == to_number:
        return jsonify({'success': False, 'error': 'Cannot swap player with itself'}), 400

    try:
        # 두 선수 찾기
        player_from = Lineup.query.filter_by(
            game_id=game_id,
            team=from_team,
            number=from_number
        ).first()

        player_to = Lineup.query.filter_by(
            game_id=game_id,
            team=to_team,
            number=to_number
        ).first()

        if not player_from:
            return jsonify({'success': False, 'error': f'Player {from_team} #{from_number} not found'}), 404

        # player_to가 없으면 단순 이동 (빈 자리로 이동)
        if not player_to:
            # 목적지 번호가 이미 사용중인지 확인
            existing = Lineup.query.filter_by(
                game_id=game_id,
                team=to_team,
                number=to_number
            ).first()

            if existing:
                return jsonify({'success': False, 'error': f'Number {to_number} is already taken in {to_team}'}), 400

            # 같은 팀 내에서 이동하는 경우 번호 재정렬
            if from_team == to_team:
                old_number = player_from.number
                new_number = to_number

                # 임시 번호로 변경 (unique constraint 회피)
                player_from.number = -1
                db.session.flush()

                if old_number < new_number:
                    # 뒤로 이동: old_number+1 ~ new_number 사이의 선수들을 -1
                    middle_players = Lineup.query.filter(
                        Lineup.game_id == game_id,
                        Lineup.team == from_team,
                        Lineup.number > old_number,
                        Lineup.number <= new_number
                    ).order_by(Lineup.number).all()

                    # 1단계: 모두 임시 음수로 변경
                    for i, p in enumerate(middle_players):
                        p.number = -(i + 2)  # -2부터 시작 (-1은 player_from이 사용중)
                    db.session.flush()

                    # 2단계: 정상 번호로 변경 (old_number부터 시작)
                    for i, p in enumerate(middle_players):
                        p.number = old_number + i
                    db.session.flush()
                else:
                    # 앞으로 이동: new_number ~ old_number-1 사이의 선수들을 +1
                    middle_players = Lineup.query.filter(
                        Lineup.game_id == game_id,
                        Lineup.team == from_team,
                        Lineup.number >= new_number,
                        Lineup.number < old_number
                    ).order_by(Lineup.number).all()

                    # 1단계: 모두 임시 음수로 변경
                    for i, p in enumerate(middle_players):
                        p.number = -(i + 2)
                    db.session.flush()

                    # 2단계: 정상 번호로 변경 (new_number+1부터 시작)
                    for i, p in enumerate(middle_players):
                        p.number = new_number + i + 1
                    db.session.flush()

                # 최종 위치로 이동
                player_from.number = new_number
                db.session.commit()
            else:
                # 다른 팀으로 이동하는 경우
                old_team = player_from.team
                old_number = player_from.number

                # player_from을 임시로 이동
                player_from.team = to_team
                player_from.number = -1
                db.session.flush()

                # 원래 팀에서 뒤의 번호들 재정렬
                later_lineups = Lineup.query.filter(
                    Lineup.game_id == game_id,
                    Lineup.team == old_team,
                    Lineup.number > old_number
                ).order_by(Lineup.number).all()

                # 1단계: 모두 임시 음수로 변경
                for i, l in enumerate(later_lineups):
                    l.number = -(i + 2)
                db.session.flush()

                # 2단계: 정상 번호로 변경 (old_number부터 시작)
                for i, l in enumerate(later_lineups):
                    l.number = old_number + i
                db.session.flush()

                # 최종 위치로 이동
                player_from.number = to_number
                db.session.commit()
        else:
            # 순번 및 팀 교체 (unique constraint 회피를 위해 임시 값 사용)
            # 1. player_from을 임시 번호로 변경
            temp_number = -1
            temp_team = player_from.team
            player_from.number = temp_number
            db.session.flush()

            # 2. player_to를 player_from의 원래 위치로 변경
            player_to.team = from_team
            player_to.number = from_number
            db.session.flush()

            # 3. player_from을 player_to의 원래 위치로 변경
            player_from.team = to_team
            player_from.number = to_number

            db.session.commit()

        # 업데이트된 라인업 조회 (영향받은 팀들)
        affected_teams = {from_team, to_team}
        updated_lineups = {}

        for team in affected_teams:
            lineups = Lineup.query.filter_by(
                game_id=game_id,
                team=team,
                arrived=True
            ).order_by(Lineup.number).all()
            updated_lineups[team] = [l.to_dict() for l in lineups]

        # WebSocket 브로드캐스트 (영향받은 팀들)
        for team in affected_teams:
            emit_game_update(game_id, 'lineup_swapped', {
                'team': team,
                'lineups': updated_lineups[team]
            })

        return jsonify({
            'success': True,
            'message': 'Lineup swapped successfully',
            'data': {
                'affected_teams': list(affected_teams),
                'lineups': updated_lineups,
                'swapped': {
                    'from': {'team': from_team, 'number': from_number, 'member': player_to.member},
                    'to': {'team': to_team, 'number': to_number, 'member': player_from.member}
                }
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/start', methods=['POST'])
def start_quarter(game_id):
    """
    쿼터 시작 (수동 선택 필수)
    Body: {
        "quarter_number": 1 (optional, 기본값: 현재 쿼터 + 1),
        "playing_blue": [1,2,3,4,5] (required),
        "bench_blue": [6,7,8] (optional),
        "playing_white": [1,2,3,4,5] (required),
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
        # 수동 선택 필수
        if 'playing_blue' not in data or 'playing_white' not in data:
            return jsonify({
                'success': False,
                'error': 'playing_blue and playing_white are required'
            }), 400

        playing_blue = data.get('playing_blue', [])
        bench_blue = data.get('bench_blue', [])
        playing_white = data.get('playing_white', [])
        bench_white = data.get('bench_white', [])

        # 유효성 검사 - 선택된 선수가 정확히 5명인지
        if len(playing_blue) != 5 or len(playing_white) != 5:
            return jsonify({
                'success': False,
                'error': 'Each team must have exactly 5 playing players'
            }), 400

        # 현재 라인업 조회
        blue_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='블루',
            arrived=True
        ).all()

        white_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='화이트',
            arrived=True
        ).all()

        # 유효성 검사 - 각 팀에 최소 5명 이상 있는지 확인
        if len(blue_lineups) < 5:
            return jsonify({
                'success': False,
                'error': f'HOME team must have at least 5 players. Currently: {len(blue_lineups)} players'
            }), 400

        if len(white_lineups) < 5:
            return jsonify({
                'success': False,
                'error': f'AWAY team must have at least 5 players. Currently: {len(white_lineups)} players'
            }), 400

        # 라인업 스냅샷 생성 (JSON 호환을 위해 키를 문자열로 저장)
        lineup_snapshot = {
            '블루': {str(lineup.number): lineup.member for lineup in blue_lineups},
            '화이트': {str(lineup.number): lineup.member for lineup in white_lineups}
        }
        print(f'[Quarter Start] Snapshot created for Q{quarter_number}:')
        print(f'  블루: {lineup_snapshot["블루"]}')
        print(f'  화이트: {lineup_snapshot["화이트"]}')

        # 쿼터 생성
        quarter = Quarter(
            game_id=game_id,
            quarter_number=quarter_number,
            status='진행중',
            playing_blue=playing_blue,
            playing_white=playing_white,
            bench_blue=bench_blue,
            bench_white=bench_white,
            lineup_snapshot=lineup_snapshot,
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
