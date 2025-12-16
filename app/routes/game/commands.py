"""
경기 관리 API 엔드포인트
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from app.models import db, Game, Lineup, Quarter, Room
from app import socketio
from app.utils import generate_guest_id
from app.routes.admin.auth import require_admin
import uuid

bp = Blueprint('game', __name__, url_prefix='/api/game')


def generate_game_id():
    """8자리 고유 게임 ID 생성"""
    return str(uuid.uuid4())[:8].upper()


def generate_room_id():
    """8자리 고유 방 ID 생성"""
    return str(uuid.uuid4())[:8].upper()


def get_or_create_room(room_name):
    """
    방 이름으로 방을 조회하거나 없으면 생성
    Returns: room_id (str)
    """
    # 기존 방 조회
    room = Room.query.filter_by(name=room_name).first()

    if room:
        return room.room_id

    # 새 방 생성
    room_id = generate_room_id()
    while Room.query.filter_by(room_id=room_id).first():
        room_id = generate_room_id()

    new_room = Room(
        room_id=room_id,
        name=room_name
    )

    db.session.add(new_room)
    db.session.flush()  # room_id를 확정하지만 아직 커밋하지 않음

    return room_id


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
@require_admin
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

    try:
        # 방 조회 또는 생성
        room_id = get_or_create_room(room)

        # 게임 생성
        game = Game(
            game_id=game_id,
            room_id=room_id,
            room=room,
            creator=creator,
            date=game_date,
            status='준비중',
            current_quarter=0
        )

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
        from sqlalchemy.exc import OperationalError, ProgrammingError

        # 테이블이 존재하지 않는 경우 자동 생성 후 재시도
        if isinstance(e, (OperationalError, ProgrammingError)):
            print(f"[/api/game/create] Database error (table might not exist): {str(e)}")
            print("[/api/game/create] Attempting to create tables...")

            try:
                db.session.rollback()

                # 테이블 생성
                from flask import current_app
                with current_app.app_context():
                    db.create_all()
                print("[/api/game/create] Tables created successfully")

                # 방 조회 또는 생성
                room_id = get_or_create_room(room)

                # 새로운 game 객체 생성 (기존 객체는 rollback으로 무효화됨)
                new_game = Game(
                    game_id=game_id,
                    room_id=room_id,
                    room=room,
                    creator=creator,
                    date=game_date,
                    status='준비중',
                    current_quarter=0
                )

                db.session.add(new_game)
                db.session.commit()

                frontend_url = get_frontend_url()
                game_url = f"{frontend_url}/game/{game_id}"

                return jsonify({
                    'success': True,
                    'data': {
                        'game_id': game_id,
                        'url': game_url,
                        'game': new_game.to_dict()
                    }
                }), 201

            except Exception as retry_error:
                print(f"[/api/game/create] Retry failed: {str(retry_error)}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Failed to create game after table creation: {str(retry_error)}'}), 500

        # 그 외 에러는 500으로 반환
        print(f"[/api/game/create] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
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
                'room_id': game.room_id,
                'room_url': f"{frontend_url}/room/{game.room_id}",
                'creator': game.creator,
                'date': game.date.isoformat() if game.date else None,
                'created_at': game.created_at.isoformat() + 'Z' if game.created_at else None,
                'status': game.status,
                'current_quarter': game.current_quarter,
                'winner': game.winner,
                'final_score_home': game.final_score_home,
                'final_score_away': game.final_score_away
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
        from sqlalchemy.exc import OperationalError, ProgrammingError

        # 테이블이 존재하지 않는 경우 빈 결과 반환
        if isinstance(e, (OperationalError, ProgrammingError)):
            print(f"[/api/game/all] Database error (table might not exist): {str(e)}")
            return jsonify({
                'success': True,
                'data': {
                    'games': [],
                    'pagination': {
                        'page': 1,
                        'limit': limit if 'limit' in locals() else 10,
                        'total_items': 0,
                        'total_pages': 0,
                        'has_next': False,
                        'has_prev': False
                    }
                }
            }), 200

        # 그 외 에러는 500으로 반환
        print(f"[/api/game/all] Unexpected error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/rooms', methods=['GET'])
def get_rooms():
    """
    모든 방 목록 조회
    rooms 테이블에서 모든 방 목록을 반환합니다.
    """
    try:
        from app.models import Room

        # rooms 테이블에서 모든 방 조회
        rooms = Room.query.order_by(Room.name).all()

        # 방 이름 리스트로 변환
        room_list = [room.name for room in rooms]

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
        'home': [l.to_dict() for l in lineups if l.team == 'home'],
        'away': [l.to_dict() for l in lineups if l.team == 'away']
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

    data = request.get_json() or {}
    team_home = data.get('team_home')
    team_away = data.get('team_away')

    # 팀이 이미 설정되어 있는지 확인 (이어하기 경기 등)
    teams_already_set = bool(game.team_home and game.team_away)

    if teams_already_set:
        # 이미 팀이 설정되어 있으면 기존 팀 사용 (이어하기 경기)
        team_home = game.team_home
        team_away = game.team_away
    else:
        # 팀이 설정되지 않았으면 Body에서 필수로 받아야 함
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

        # 팀이 아직 설정되지 않았으면 설정
        if not teams_already_set:
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
        total_home = last_quarter.score_home
        total_away = last_quarter.score_away

        # 승자 결정
        if total_home > total_away:
            winner = 'home'
        elif total_away > total_home:
            winner = 'away'
        else:
            winner = '무승부'

        game.status = '종료'
        game.ended_at = datetime.utcnow()
        game.final_score_home = total_home
        game.final_score_away = total_away
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
@require_admin
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


@bp.route('/<game_id>/copy', methods=['POST'])
@require_admin
def copy_game(game_id):
    """
    이전 경기를 복사해서 새 경기 생성 (라인업 포함)
    원본 경기의 라인업, 팀 배정을 그대로 복사합니다.
    """
    # 원본 경기 조회
    original_game = Game.query.filter_by(game_id=game_id).first()

    if not original_game:
        return jsonify({'success': False, 'error': 'Original game not found'}), 404

    # 원본 라인업 조회
    original_lineups = Lineup.query.filter_by(game_id=game_id).order_by(Lineup.team, Lineup.number).all()

    if not original_lineups:
        return jsonify({'success': False, 'error': 'Original game has no lineup'}), 400

    try:
        # 새 게임 ID 생성
        new_game_id = generate_game_id()
        while Game.query.filter_by(game_id=new_game_id).first():
            new_game_id = generate_game_id()

        # 새 게임 생성
        new_game = Game(
            game_id=new_game_id,
            room_id=original_game.room_id,
            room=original_game.room,
            creator='Admin (이어하기)',
            date=date.today(),
            status='준비중',
            current_quarter=0,
            team_home=original_game.team_home,
            team_away=original_game.team_away
        )
        db.session.add(new_game)
        db.session.flush()

        # 라인업 복사
        for original_lineup in original_lineups:
            new_lineup = Lineup(
                game_id=new_game_id,
                member_id=original_lineup.member_id,
                is_guest=original_lineup.is_guest,
                team_id_snapshot=original_lineup.team_id_snapshot,
                team=original_lineup.team,
                member=original_lineup.member,
                number=original_lineup.number,
                arrived=True,  # 이어하기는 이전 경기 참여 선수들이므로 arrived=True
                arrived_at=datetime.utcnow(),
                playing_status='playing'
            )
            db.session.add(new_lineup)

        db.session.commit()

        # 게임 URL 생성
        frontend_url = get_frontend_url()
        game_url = f"{frontend_url}/game/{new_game_id}"

        return jsonify({
            'success': True,
            'data': {
                'game_id': new_game_id,
                'url': game_url,
                'game': new_game.to_dict(),
                'copied_players': len(original_lineups)
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/lineup/arrival', methods=['POST'])
def player_arrival(game_id):
    """
    선수 도착 처리
    Body: {
        "team": "home" or "away",
        "member": "선수 이름",
        "member_id": "MEM_X7Y2K9P3" (optional, 프리셋 멤버인 경우),
        "team_id": "TEAM_X7Y2K9P3" (optional, 멤버의 팀 ID)
    }
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    data = request.get_json()
    team = data.get('team')
    member_name = data.get('member')
    member_id = data.get('member_id')  # 프리셋 멤버면 존재
    team_id = data.get('team_id')  # 멤버의 팀 ID

    if team not in ['home', 'away']:
        return jsonify({'success': False, 'error': 'team must be "home" or "away"'}), 400

    if not member_name:
        return jsonify({'success': False, 'error': 'member is required'}), 400

    # 중복 체크: member_id가 있으면 member_id로, 없으면 이름으로
    if member_id:
        existing_player = Lineup.query.filter_by(
            game_id=game_id,
            member_id=member_id,
            arrived=True
        ).first()
    else:
        existing_player = Lineup.query.filter_by(
            game_id=game_id,
            member=member_name,
            arrived=True
        ).first()

    if existing_player:
        error_msg = f'{member_name}'
        if member_id:
            error_msg += f' #{member_id[-4:]}'
        error_msg += f'님은 이미 {existing_player.team} 팀에 출석했습니다.'
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

    try:
        # 게스트 여부 판단
        is_guest = not bool(member_id)

        # 게스트인 경우 임시 ID 발급
        if is_guest:
            member_id = generate_guest_id()

        # 해당 팀의 다음 번호 계산
        last_lineup = Lineup.query.filter_by(
            game_id=game_id,
            team=team
        ).order_by(Lineup.number.desc()).first()

        next_number = (last_lineup.number + 1) if last_lineup else 1

        # 라인업 추가
        lineup = Lineup(
            game_id=game_id,
            member_id=member_id,
            is_guest=is_guest,
            team_id_snapshot=team_id,
            team=team,
            member=member_name,
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
        db.session.flush()

        # 뒤의 번호들 재정렬 (2단계 업데이트로 unique constraint 회피)
        later_lineups = Lineup.query.filter(
            Lineup.game_id == game_id,
            Lineup.team == team,
            Lineup.number > number
        ).order_by(Lineup.number).all()

        # 1단계: 모두 임시 음수로 변경
        for i, l in enumerate(later_lineups):
            l.number = -(i + 1)
        db.session.flush()

        # 2단계: 정상 번호로 변경 (삭제된 번호부터 시작)
        for i, l in enumerate(later_lineups):
            l.number = number + i
        db.session.flush()

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


@bp.route('/<game_id>/lineup/<int:lineup_id>/toggle-status', methods=['PUT'])
def toggle_playing_status(game_id, lineup_id):
    """
    출전/벤치 상태 토글
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    # 진행중인 쿼터가 있으면 토글 불가
    ongoing_quarter = Quarter.query.filter_by(
        game_id=game_id,
        status='진행중'
    ).first()

    if ongoing_quarter:
        return jsonify({'success': False, 'error': 'Cannot toggle status while quarter is ongoing'}), 400

    lineup = Lineup.query.filter_by(id=lineup_id, game_id=game_id).first()

    if not lineup:
        return jsonify({'success': False, 'error': 'Lineup not found'}), 404

    try:
        # 상태 토글
        lineup.playing_status = 'bench' if lineup.playing_status == 'playing' else 'playing'
        db.session.commit()

        # 업데이트된 팀의 전체 라인업 조회
        team = lineup.team
        updated_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team=team,
            arrived=True
        ).order_by(Lineup.number).all()

        # WebSocket 브로드캐스트 (전체 라인업 업데이트)
        emit_game_update(game_id, 'lineup_updated', {
            'team': team,
            'lineups': [l.to_dict() for l in updated_lineups]
        })

        return jsonify({
            'success': True,
            'data': lineup.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/lineup/swap', methods=['PUT'])
def swap_lineup_numbers(game_id):
    """
    순번 교체 (드래그앤드롭) - 같은 팀 또는 다른 팀 간 교체 지원
    Body: {
        "from_team": "home",
        "from_number": 5,
        "to_team": "away",
        "to_number": 3
    }

    또는 기존 호환성을 위한 형식:
    Body: {
        "team": "home",
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
    from_team = data.get('from_team') or data.get('team1')
    from_number = data.get('from_number') or data.get('number1')
    to_team = data.get('to_team') or data.get('team2')
    to_number = data.get('to_number') or data.get('number2')

    # 기존 형식 호환 (같은 팀 내 교체)
    if not from_team or not to_team:
        team = data.get('team')
        if team:
            from_team = team
            to_team = team

    # 팀 검증
    valid_teams = ['home', 'away']
    if from_team not in valid_teams or to_team not in valid_teams:
        return jsonify({'success': False, 'error': 'teams must be "home" or "away"'}), 400

    if not from_number or not to_number:
        return jsonify({'success': False, 'error': 'from_number and to_number are required'}), 400

    if from_team == to_team and from_number == to_number:
        return jsonify({'success': False, 'error': 'Cannot swap player with itself'}), 400

    # 경기 상태에 따라 arrived 필터 결정
    # 준비중: 모든 라인업 대상 (이어하기 경기 지원)
    # 진행중/종료: arrived=True만 대상
    use_arrived_filter = game.status != '준비중'

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
                # 팀에 선수가 1명뿐이면 이동할 필요 없음
                query = Lineup.query.filter_by(
                    game_id=game_id,
                    team=from_team
                )
                if use_arrived_filter:
                    query = query.filter_by(arrived=True)
                team_player_count = query.count()

                if team_player_count == 1:
                    return jsonify({
                        'success': False,
                        'error': 'Cannot move player within a team with only one player'
                    }), 400

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
                db.session.flush()

                # 같은 팀 내에서도 번호를 1부터 재정렬 (빈 순번 방지)
                query = Lineup.query.filter_by(
                    game_id=game_id,
                    team=from_team
                )
                if use_arrived_filter:
                    query = query.filter_by(arrived=True)
                team_lineups = query.order_by(Lineup.number).all()

                # 1단계: 모두 임시 음수로 변경
                for i, l in enumerate(team_lineups):
                    l.number = -(i + 100)
                db.session.flush()

                # 2단계: 1부터 연속적으로 재정렬
                for i, l in enumerate(team_lineups):
                    l.number = i + 1
                db.session.flush()

                db.session.commit()
            else:
                # 다른 팀으로 이동하는 경우
                old_team = player_from.team
                old_number = player_from.number

                # 1단계: player_from을 임시 위치로 이동
                player_from.team = to_team
                player_from.number = -1
                db.session.flush()

                # 2단계: 원래 팀에서 뒤의 번호들 -1 (빈 공간 메우기)
                query = Lineup.query.filter(
                    Lineup.game_id == game_id,
                    Lineup.team == old_team,
                    Lineup.number > old_number
                )
                if use_arrived_filter:
                    query = query.filter(Lineup.arrived == True)
                later_lineups = query.order_by(Lineup.number).all()

                for i, l in enumerate(later_lineups):
                    l.number = -(i + 2)
                db.session.flush()

                for i, l in enumerate(later_lineups):
                    l.number = old_number + i
                db.session.flush()

                # 3단계: 새 팀에서 to_number 이상인 선수들을 임시 음수로 변경 후 +1
                query = Lineup.query.filter(
                    Lineup.game_id == game_id,
                    Lineup.team == to_team,
                    Lineup.number >= to_number
                )
                if use_arrived_filter:
                    query = query.filter(Lineup.arrived == True)
                new_team_later_lineups = query.order_by(Lineup.number).all()

                # 임시 음수로 변경
                for i, l in enumerate(new_team_later_lineups):
                    l.number = -(i + 100)
                db.session.flush()

                # +1 하여 공간 만들기
                for i, l in enumerate(new_team_later_lineups):
                    l.number = to_number + i + 1
                db.session.flush()

                # 4단계: player_from을 최종 위치로 이동
                player_from.number = to_number
                db.session.flush()

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
            query = Lineup.query.filter_by(
                game_id=game_id,
                team=team
            )
            if use_arrived_filter:
                query = query.filter_by(arrived=True)
            lineups = query.order_by(Lineup.number).all()
            updated_lineups[team] = [l.to_dict() for l in lineups]

        # WebSocket 브로드캐스트 (한 번에 모든 영향받은 팀의 라인업 전송)
        emit_game_update(game_id, 'lineup_swapped', {
            'affected_teams': list(affected_teams),
            'lineups': updated_lineups
        })

        # 응답 데이터 구성
        response_data = {
            'success': True,
            'message': 'Lineup swapped successfully',
            'data': {
                'affected_teams': list(affected_teams),
                'lineups': updated_lineups
            }
        }

        # player_to가 있는 경우에만 swapped 정보 추가
        if player_to:
            response_data['data']['swapped'] = {
                'from': {'team': from_team, 'number': from_number, 'member': player_to.member},
                'to': {'team': to_team, 'number': to_number, 'member': player_from.member}
            }

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/start', methods=['POST'])
def start_quarter(game_id):
    """
    쿼터 시작 (수동 선택 필수)
    Body: {
        "quarter_number": 1 (optional, 기본값: 현재 쿼터 + 1),
        "playing_home": [1,2,3,4,5] (required),
        "bench_home": [6,7,8] (optional),
        "playing_away": [1,2,3,4,5] (required),
        "bench_away": [6,7,8] (optional)
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
        if 'playing_home' not in data or 'playing_away' not in data:
            return jsonify({
                'success': False,
                'error': 'playing_home and playing_away are required'
            }), 400

        playing_home = data.get('playing_home', [])
        bench_home = data.get('bench_home', [])
        playing_away = data.get('playing_away', [])
        bench_away = data.get('bench_away', [])

        # 유효성 검사 - 선택된 선수가 정확히 5명인지
        if len(playing_home) != 5 or len(playing_away) != 5:
            return jsonify({
                'success': False,
                'error': 'Each team must have exactly 5 playing players'
            }), 400

        # 현재 라인업 조회
        home_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='home',
            arrived=True
        ).all()

        away_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='away',
            arrived=True
        ).all()

        # 유효성 검사 - 각 팀에 최소 5명 이상 있는지 확인
        if len(home_lineups) < 5:
            return jsonify({
                'success': False,
                'error': f'HOME team must have at least 5 players. Currently: {len(home_lineups)} players'
            }), 400

        if len(away_lineups) < 5:
            return jsonify({
                'success': False,
                'error': f'AWAY team must have at least 5 players. Currently: {len(away_lineups)} players'
            }), 400

        # 라인업 스냅샷 생성 (이름과 member_id 함께 저장)
        lineup_snapshot = {
            'home': {
                str(lineup.number): {
                    'name': lineup.member,
                    'member_id': lineup.member_id,
                    'is_guest': lineup.is_guest
                } for lineup in home_lineups
            },
            'away': {
                str(lineup.number): {
                    'name': lineup.member,
                    'member_id': lineup.member_id,
                    'is_guest': lineup.is_guest
                } for lineup in away_lineups
            }
        }
        print(f'[Quarter Start] Snapshot created for Q{quarter_number}:')
        print(f'  home: {len(lineup_snapshot["home"])}명')
        print(f'  away: {len(lineup_snapshot["away"])}명')

        # 이전 쿼터의 점수 가져오기
        previous_quarter = Quarter.query.filter_by(
            game_id=game_id,
            quarter_number=quarter_number - 1
        ).first()

        if previous_quarter:
            initial_score_home = previous_quarter.score_home
            initial_score_away = previous_quarter.score_away
            print(f'[Quarter Start] Inheriting scores from Q{quarter_number - 1}: home {initial_score_home} - away {initial_score_away}')
        else:
            initial_score_home = 0
            initial_score_away = 0
            print(f'[Quarter Start] First quarter, starting from 0-0')

        # 쿼터 생성
        quarter = Quarter(
            game_id=game_id,
            quarter_number=quarter_number,
            status='진행중',
            playing_home=playing_home,
            playing_away=playing_away,
            bench_home=bench_home,
            bench_away=bench_away,
            lineup_snapshot=lineup_snapshot,
            score_home=initial_score_home,
            score_away=initial_score_away,
            started_at=datetime.utcnow()
        )

        db.session.add(quarter)
        game.current_quarter = quarter_number

        # 쿼터 시작 시 라인업의 playing_status 업데이트
        playing_numbers_home = set(playing_home)
        playing_numbers_away = set(playing_away)

        # home팀 업데이트
        for lineup in home_lineups:
            if lineup.number in playing_numbers_home:
                lineup.playing_status = 'playing'
            else:
                lineup.playing_status = 'bench'

        # away팀 업데이트
        for lineup in away_lineups:
            if lineup.number in playing_numbers_away:
                lineup.playing_status = 'playing'
            else:
                lineup.playing_status = 'bench'

        db.session.commit()

        # WebSocket 브로드캐스트 (쿼터 시작)
        emit_game_update(game_id, 'quarter_started', quarter.to_dict())

        # WebSocket 브로드캐스트 (라인업 업데이트)
        updated_home = Lineup.query.filter_by(
            game_id=game_id,
            team='home',
            arrived=True
        ).order_by(Lineup.number).all()

        updated_away = Lineup.query.filter_by(
            game_id=game_id,
            team='away',
            arrived=True
        ).order_by(Lineup.number).all()

        emit_game_update(game_id, 'lineup_updated', {
            'team': 'home',
            'lineups': [l.to_dict() for l in updated_home]
        })
        emit_game_update(game_id, 'lineup_updated', {
            'team': 'away',
            'lineups': [l.to_dict() for l in updated_away]
        })

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

        # 쿼터 종료 후 출전/벤치 상태 업데이트
        # playing_home, playing_away에 있던 선수들은 'playing'으로, 나머지는 'bench'로 업데이트
        playing_numbers_home = set(quarter.playing_home or [])
        playing_numbers_away = set(quarter.playing_away or [])

        # home팀 업데이트
        home_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='home',
            arrived=True
        ).all()

        for lineup in home_lineups:
            if lineup.number in playing_numbers_home:
                lineup.playing_status = 'playing'
            else:
                lineup.playing_status = 'bench'

        # away팀 업데이트
        away_lineups = Lineup.query.filter_by(
            game_id=game_id,
            team='away',
            arrived=True
        ).all()

        for lineup in away_lineups:
            if lineup.number in playing_numbers_away:
                lineup.playing_status = 'playing'
            else:
                lineup.playing_status = 'bench'

        db.session.commit()

        # WebSocket 브로드캐스트 (쿼터 종료)
        emit_game_update(game_id, 'quarter_ended', quarter.to_dict())

        # WebSocket 브로드캐스트 (라인업 업데이트)
        updated_home = Lineup.query.filter_by(
            game_id=game_id,
            team='home',
            arrived=True
        ).order_by(Lineup.number).all()

        updated_away = Lineup.query.filter_by(
            game_id=game_id,
            team='away',
            arrived=True
        ).order_by(Lineup.number).all()

        emit_game_update(game_id, 'lineup_updated', {
            'team': 'home',
            'lineups': [l.to_dict() for l in updated_home]
        })
        emit_game_update(game_id, 'lineup_updated', {
            'team': 'away',
            'lineups': [l.to_dict() for l in updated_away]
        })

        return jsonify({
            'success': True,
            'data': quarter.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/<int:quarter_number>/cancel', methods=['DELETE'])
def cancel_quarter(game_id, quarter_number):
    """
    쿼터 취소 (진행중인 쿼터만 취소 가능)
    """
    game = Game.query.filter_by(game_id=game_id).first()

    if not game:
        return jsonify({'success': False, 'error': 'Game not found'}), 404

    quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if not quarter:
        return jsonify({'success': False, 'error': 'Quarter not found'}), 404

    # 진행중인 쿼터만 취소 가능
    if quarter.status != '진행중':
        return jsonify({'success': False, 'error': 'Only ongoing quarters can be cancelled'}), 400

    try:
        # 쿼터 삭제
        db.session.delete(quarter)

        # 현재 쿼터 번호 조정 (이전 쿼터로 되돌림)
        if game.current_quarter == quarter_number:
            game.current_quarter = quarter_number - 1

        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'quarter_cancelled', {
            'quarter_number': quarter_number,
            'current_quarter': game.current_quarter
        })

        return jsonify({
            'success': True,
            'message': f'Quarter {quarter_number} cancelled successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<game_id>/quarter/<int:quarter_number>/score', methods=['PUT'])
def update_score(game_id, quarter_number):
    """
    쿼터 점수 업데이트
    Body: {
        "score_home": 10,
        "score_away": 8
    }
    """
    quarter = Quarter.query.filter_by(
        game_id=game_id,
        quarter_number=quarter_number
    ).first()

    if not quarter:
        return jsonify({'success': False, 'error': 'Quarter not found'}), 404

    data = request.get_json()
    score_home = data.get('score_home')
    score_away = data.get('score_away')

    if score_home is None or score_away is None:
        return jsonify({'success': False, 'error': 'Both score_home and score_away are required'}), 400

    try:
        quarter.score_home = score_home
        quarter.score_away = score_away
        db.session.commit()

        # WebSocket 브로드캐스트
        emit_game_update(game_id, 'score_updated', {
            'quarter': quarter_number,
            'score_home': score_home,
            'score_away': score_away
        })

        return jsonify({
            'success': True,
            'data': quarter.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
