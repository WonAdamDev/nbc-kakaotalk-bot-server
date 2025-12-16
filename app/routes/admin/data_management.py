"""
Admin 데이터 관리 API - Import/Export
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from app.routes.admin.auth import require_admin
from app.models import db, Room, Team, Member
from app.utils import generate_member_id, generate_team_id
from datetime import datetime
import pandas as pd
import io
import time
import logging
import uuid

bp = Blueprint('data_management', __name__, url_prefix='/api/admin/data')

logger = logging.getLogger(__name__)

# 파일 크기 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def generate_room_id():
    """8자리 고유 방 ID 생성"""
    return str(uuid.uuid4())[:8].upper()


def validate_excel_file(file):
    """Excel 파일 검증"""
    if not file:
        return False, "파일을 선택해주세요"

    # 파일 확장자 체크
    filename = file.filename
    if not filename.endswith(('.xlsx', '.xls')):
        return False, ".xlsx 또는 .xls 파일만 지원됩니다"

    # 파일 크기 체크 (메모리에서)
    file.seek(0, 2)  # 끝으로 이동
    file_size = file.tell()
    file.seek(0)  # 다시 처음으로

    if file_size > MAX_FILE_SIZE:
        return False, "파일 크기는 10MB 이하여야 합니다"

    return True, None


def validate_dataframe(df):
    """DataFrame 데이터 검증"""
    errors = []

    # 필수 컬럼 체크
    required_cols = ['room', 'member', 'team']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return False, f"필수 컬럼 누락: {', '.join(missing_cols)}"

    # 행별 검증
    for index, row in df.iterrows():
        row_num = index + 2  # Excel 행 번호 (헤더 + 0-index)
        row_errors = []

        # room 필수
        if pd.isna(row['room']) or str(row['room']).strip() == '':
            row_errors.append("room은 필수입니다")

        # member 필수
        if pd.isna(row['member']) or str(row['member']).strip() == '':
            row_errors.append("member는 필수입니다")

        # ID 형식 검증 (있는 경우에만)
        if 'team_id' in df.columns and not pd.isna(row.get('team_id')):
            team_id = str(row['team_id']).strip()
            if team_id and not team_id.startswith('TEAM_'):
                row_errors.append(f"잘못된 team_id 형식: {team_id}")

        if 'member_id' in df.columns and not pd.isna(row.get('member_id')):
            member_id = str(row['member_id']).strip()
            if member_id and not member_id.startswith('MEM_'):
                row_errors.append(f"잘못된 member_id 형식: {member_id}")

        if row_errors:
            errors.append({
                'row': row_num,
                'error': ', '.join(row_errors)
            })

    if errors:
        return False, errors

    return True, None


@bp.route('/import', methods=['POST'])
@require_admin
def import_data():
    """
    Excel 파일로 멤버/팀 데이터 Import
    """
    start_time = time.time()

    try:
        # 모드 파라미터 확인
        replace_all = request.form.get('replace_all', 'false').lower() == 'true'
        update_merge = request.form.get('update_merge', 'false').lower() == 'true'

        # 모드 충돌 체크
        if replace_all and update_merge:
            return jsonify({
                'success': False,
                'message': 'Replace All과 Update/Merge 모드를 동시에 사용할 수 없습니다.'
            }), 400

        # 파일 가져오기
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '파일이 없습니다.'
            }), 400

        file = request.files['file']

        # 파일 검증
        is_valid, error_msg = validate_excel_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400

        # Excel 파싱
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            logger.error(f"[IMPORT] Excel parsing error: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Excel 파일을 읽을 수 없습니다: {str(e)}'
            }), 400

        # 데이터 검증
        is_valid, validation_errors = validate_dataframe(df)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': '데이터 검증 실패',
                'data': {
                    'errors': validation_errors
                }
            }), 400

        # 데이터 정제
        df['room'] = df['room'].astype(str).str.strip()
        df['member'] = df['member'].astype(str).str.strip()
        df['team'] = df['team'].fillna('').astype(str).str.strip()
        if 'team_id' in df.columns:
            df['team_id'] = df['team_id'].fillna('').astype(str).str.strip()
        else:
            df['team_id'] = ''
        if 'member_id' in df.columns:
            df['member_id'] = df['member_id'].fillna('').astype(str).str.strip()
        else:
            df['member_id'] = ''

        # 통계 초기화
        mode_name = 'replace_all' if replace_all else ('update_merge' if update_merge else 'append')
        stats = {
            'mode': mode_name,
            'total_rows': len(df),
            'rooms_created': 0,
            'rooms_skipped': 0,
            'teams_created': 0,
            'teams_updated': 0,
            'teams_skipped': 0,
            'members_created': 0,
            'members_updated': 0,
            'members_skipped': 0,
            'errors': []
        }

        # Replace All 모드 처리
        if replace_all:
            logger.warning("[IMPORT] REPLACE_ALL mode - Deleting all rooms, members and teams")

            # PostgreSQL 전체 삭제 (CASCADE로 members, teams도 함께 삭제됨)
            try:
                deleted_members = db.session.query(Member).delete()
                deleted_teams = db.session.query(Team).delete()
                deleted_rooms = db.session.query(Room).delete()
                db.session.commit()

                stats['deleted_members'] = deleted_members
                stats['deleted_teams'] = deleted_teams
                stats['deleted_rooms'] = deleted_rooms

                logger.info(f"[IMPORT] Deleted {deleted_rooms} rooms, {deleted_teams} teams, {deleted_members} members")
            except Exception as e:
                db.session.rollback()
                logger.error(f"[IMPORT] PostgreSQL delete error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'데이터 삭제 실패: {str(e)}'
                }), 500

        # Room 처리 (PostgreSQL)
        if update_merge:
            # Update/Merge 모드: Room은 생성하지 않고, 존재 여부만 검증
            logger.info("[IMPORT] UPDATE_MERGE mode - Validating existing rooms only")
            unique_rooms = df['room'].unique()
            for room_name in unique_rooms:
                existing_room = Room.query.filter_by(name=room_name).first()
                if not existing_room:
                    return jsonify({
                        'success': False,
                        'message': f'Room "{room_name}"이(가) 존재하지 않습니다. Update/Merge 모드에서는 방을 새로 생성할 수 없습니다.'
                    }), 400
                stats['rooms_skipped'] += 1
        else:
            # Append/Replace All 모드: Room 생성
            unique_rooms = df['room'].unique()
            for room_name in unique_rooms:
                # 기존 room 확인
                existing_room = Room.query.filter_by(name=room_name).first()
                if existing_room:
                    stats['rooms_skipped'] += 1
                    logger.info(f"[IMPORT] Room exists: {room_name}, skipping")
                else:
                    # 새 room 생성
                    room_id = generate_room_id()
                    while Room.query.filter_by(room_id=room_id).first():
                        room_id = generate_room_id()

                    new_room = Room(room_id=room_id, name=room_name)
                    db.session.add(new_room)
                    stats['rooms_created'] += 1
                    logger.info(f"[IMPORT] Created room: {room_name} (ID: {room_id})")

            # PostgreSQL 커밋
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.error(f"[IMPORT] Room creation failed: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Room 생성 실패: {str(e)}'
                }), 500

        # 팀 처리 (중복 제거)
        teams_to_create = {}  # key: (room_name, team_name), value: team_id

        for _, row in df.iterrows():
            if not row['team']:  # 팀이 없으면 스킵
                continue

            room_name = row['room']
            team_name = row['team']
            team_id_from_excel = row['team_id']

            # 이미 처리한 팀이면 스킵
            if (room_name, team_name) in teams_to_create:
                continue

            # room_id 가져오기
            room = Room.query.filter_by(name=room_name).first()
            if not room:
                logger.error(f"[IMPORT] Room not found: {room_name}")
                continue

            # team_id가 지정되어 있으면 DB 확인
            if team_id_from_excel:
                existing_team = Team.query.filter_by(team_id=team_id_from_excel).first()
                if existing_team:
                    if update_merge:
                        # Update/Merge 모드: 팀 이름 업데이트
                        if existing_team.name != team_name:
                            existing_team.name = team_name
                            stats['teams_updated'] += 1
                            logger.info(f"[IMPORT] Updated team: {team_id_from_excel} -> {team_name}")
                        else:
                            stats['teams_skipped'] += 1
                            logger.info(f"[IMPORT] Team unchanged: {team_id_from_excel}")
                    else:
                        # Append 모드: 기존 팀 사용
                        stats['teams_skipped'] += 1
                        logger.info(f"[IMPORT] Team exists with ID: {team_id_from_excel}, skipping")
                    teams_to_create[(room_name, team_name)] = team_id_from_excel
                    continue
                else:
                    if update_merge:
                        # Update/Merge 모드: team_id가 있는데 DB에 없으면 에러
                        logger.error(f"[IMPORT] team_id {team_id_from_excel} not found in UPDATE_MERGE mode")
                        stats['errors'].append({
                            'row': '?',
                            'error': f'team_id {team_id_from_excel}이(가) DB에 존재하지 않습니다'
                        })
                        continue
                    else:
                        # Append 모드: DB에 없으므로 새 ID 발급
                        logger.warning(f"[IMPORT] team_id {team_id_from_excel} not found, creating with new ID")

            # team_id 미지정 또는 DB에 없음 - room_id+name으로 확인
            existing_team_by_name = Team.query.filter_by(
                room_id=room.room_id,
                name=team_name
            ).first()

            if existing_team_by_name:
                # 기존 팀 사용
                teams_to_create[(room_name, team_name)] = existing_team_by_name.team_id
                stats['teams_skipped'] += 1
            else:
                # 새 팀 생성
                new_team_id = generate_team_id()
                new_team = Team(
                    team_id=new_team_id,
                    room_id=room.room_id,
                    name=team_name
                )
                db.session.add(new_team)
                teams_to_create[(room_name, team_name)] = new_team_id
                stats['teams_created'] += 1
                logger.info(f"[IMPORT] Created team: {team_name} (ID: {new_team_id}) in room {room_name}")

        # Teams 커밋
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"[IMPORT] Team creation failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Team 생성 실패: {str(e)}'
            }), 500

        # 멤버 처리
        for index, row in df.iterrows():
            try:
                room_name = row['room']
                member_name = row['member']
                team_name = row['team']
                member_id_from_excel = row['member_id']

                # room_id 가져오기
                room = Room.query.filter_by(name=room_name).first()
                if not room:
                    logger.error(f"[IMPORT] Room not found: {room_name}")
                    stats['errors'].append({
                        'row': index + 2,
                        'error': f'Room not found: {room_name}'
                    })
                    continue

                # 팀 배정
                team_id = None
                if team_name and (room_name, team_name) in teams_to_create:
                    team_id = teams_to_create[(room_name, team_name)]

                # member_id가 지정되어 있으면 DB 확인
                if member_id_from_excel:
                    existing_member = Member.query.filter_by(member_id=member_id_from_excel).first()
                    if existing_member:
                        if update_merge:
                            # Update/Merge 모드: 멤버 정보 업데이트
                            updated = False
                            if existing_member.name != member_name:
                                existing_member.name = member_name
                                updated = True
                            if existing_member.team_id != team_id:
                                existing_member.team_id = team_id
                                updated = True

                            if updated:
                                stats['members_updated'] += 1
                                logger.info(f"[IMPORT] Updated member: {member_id_from_excel} -> {member_name} (team: {team_id})")
                            else:
                                stats['members_skipped'] += 1
                                logger.info(f"[IMPORT] Member unchanged: {member_id_from_excel}")
                        else:
                            # Append 모드: 기존 멤버 사용 (스킵)
                            stats['members_skipped'] += 1
                            logger.info(f"[IMPORT] Member exists with ID: {member_id_from_excel}, skipping")
                        continue
                    else:
                        if update_merge:
                            # Update/Merge 모드: member_id가 있는데 DB에 없으면 에러
                            logger.error(f"[IMPORT] member_id {member_id_from_excel} not found in UPDATE_MERGE mode")
                            stats['errors'].append({
                                'row': index + 2,
                                'error': f'member_id {member_id_from_excel}이(가) DB에 존재하지 않습니다'
                            })
                            continue
                        else:
                            # Append 모드: DB에 없으므로 새 ID 발급
                            logger.warning(f"[IMPORT] member_id {member_id_from_excel} not found, creating with new ID")

                # member_id 미지정 또는 DB에 없음 - room_id+name으로 확인
                existing_member_by_name = Member.query.filter_by(
                    room_id=room.room_id,
                    name=member_name
                ).first()

                if existing_member_by_name:
                    if update_merge:
                        # Update/Merge 모드: 이름으로 찾은 멤버 업데이트
                        if existing_member_by_name.team_id != team_id:
                            existing_member_by_name.team_id = team_id
                            stats['members_updated'] += 1
                            logger.info(f"[IMPORT] Updated member by name: {member_name} (team: {team_id})")
                        else:
                            stats['members_skipped'] += 1
                        continue
                    else:
                        # Append 모드: 기존 멤버 사용 (스킵)
                        stats['members_skipped'] += 1
                        continue

                # 새 멤버 생성
                new_member_id = generate_member_id()
                new_member = Member(
                    member_id=new_member_id,
                    room_id=room.room_id,
                    name=member_name,
                    team_id=team_id
                )
                db.session.add(new_member)
                stats['members_created'] += 1
                logger.info(f"[IMPORT] Created member: {member_name} (ID: {new_member_id})")

            except Exception as e:
                logger.error(f"[IMPORT] Error processing row {index + 2}: {str(e)}")
                stats['errors'].append({
                    'row': index + 2,
                    'error': str(e)
                })

        # Members 커밋
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"[IMPORT] Member creation failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Member 생성 실패: {str(e)}'
            }), 500

        # 처리 시간 계산
        processing_time = int((time.time() - start_time) * 1000)
        stats['processing_time_ms'] = processing_time

        logger.info(f"[IMPORT] Completed: {stats}")

        return jsonify({
            'success': True,
            'data': stats
        }), 200

    except Exception as e:
        logger.error(f"[IMPORT] Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500


@bp.route('/export', methods=['GET'])
@require_admin
def export_data():
    """
    전체 멤버/팀 데이터를 Excel로 Export
    """
    try:
        # 모든 멤버 조회 (JOIN으로 room, team 정보 포함)
        members = db.session.query(
            Room.name.label('room_name'),
            Member.name.label('member_name'),
            Member.member_id,
            Team.name.label('team_name'),
            Team.team_id
        ).join(
            Room, Member.room_id == Room.room_id
        ).outerjoin(
            Team, Member.team_id == Team.team_id
        ).order_by(
            Room.name, Member.name
        ).all()

        # Export 데이터 구조화
        export_data = []
        for member in members:
            export_data.append({
                'room': member.room_name,
                'member': member.member_name,
                'team': member.team_name or '',
                'team_id': member.team_id or '',
                'member_id': member.member_id
            })

        # DataFrame 생성
        df = pd.DataFrame(export_data)

        # 컬럼 순서 지정
        df = df[['room', 'member', 'team', 'team_id', 'member_id']]

        # Excel 파일 생성 (메모리에서)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Members', index=False)
        output.seek(0)

        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'nbc_members_teams_{timestamp}.xlsx'

        logger.info(f"[EXPORT] Exported {len(df)} members to {filename}")

        # 파일 전송
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"[EXPORT] Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Export 중 오류가 발생했습니다: {str(e)}'
        }), 500
