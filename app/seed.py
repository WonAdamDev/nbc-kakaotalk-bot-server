"""
DB Seeding 모듈
team.xlsx 파일에서 팀/멤버 데이터를 읽어 MongoDB와 Redis에 초기 데이터를 세팅합니다.
"""

import os
import pandas as pd
from typing import Optional


def seed_from_excel(cache_manager, excel_path: str = 'team.xlsx') -> dict:
    """
    Excel 파일에서 데이터를 읽어 DB를 seed합니다.

    Args:
        cache_manager: CacheManager 인스턴스
        excel_path: Excel 파일 경로 (기본값: 'team.xlsx')

    Returns:
        dict: seed 결과 정보
            - success: bool
            - message: str
            - stats: dict (성공 시)

    Excel 파일 형식:
        컬럼: room, member, team
        예시:
            room    member  team
            방A     철수    1팀
            방A     영희    1팀
            방A     민수    (빈값 - 팀 없음)
    """

    # 1. 파일 존재 확인
    if not os.path.exists(excel_path):
        return {
            'success': False,
            'message': f'파일을 찾을 수 없습니다: {excel_path}'
        }

    try:
        # 2. Excel 파일 읽기
        print(f"[SEED] Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path)

        # 3. 필수 컬럼 확인
        required_columns = ['room', 'member', 'team']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            return {
                'success': False,
                'message': f'필수 컬럼이 없습니다: {", ".join(missing_columns)}\n현재 컬럼: {", ".join(df.columns)}'
            }

        # 4. room과 member는 필수, team은 선택적
        # room, member가 NaN인 행 제거
        df = df.dropna(subset=['room', 'member'])

        # 문자열 변환 및 공백 제거
        df['room'] = df['room'].astype(str).str.strip()
        df['member'] = df['member'].astype(str).str.strip()
        # team은 NaN일 수 있으므로 fillna 사용
        df['team'] = df['team'].fillna('').astype(str).str.strip()

        # 5. 통계 수집
        stats = {
            'total_rows': len(df),
            'members_added': 0,
            'teams_added': 0,
            'member_team_links': 0,
            'members_without_team': 0,
            'errors': []
        }

        # 6. 팀별로 그룹화하여 처리 (빈 팀은 제외)
        teams_df = df[df['team'] != '']
        teams_per_room = teams_df.groupby(['room', 'team']).size().reset_index(name='count')

        print(f"[SEED] Processing {len(teams_per_room)} unique teams...")

        for _, team_row in teams_per_room.iterrows():
            room = team_row['room']
            team = team_row['team']
            team_key = f"room:{room}:team:{team}"

            # 팀이 이미 존재하는지 확인
            existing_team = cache_manager.get('teams', team_key)

            if not existing_team:
                cache_manager.set('teams', team_key, team)
                stats['teams_added'] += 1
                print(f"[SEED] Team created: {team_key}")

        # 7. 멤버 처리
        print(f"[SEED] Processing {len(df)} members...")

        for _, row in df.iterrows():
            room = row['room']
            member = row['member']
            team = row['team']

            member_key = f"room:{room}:member:{member}"

            try:
                # 멤버 추가
                existing_member = cache_manager.get('members', member_key)
                if not existing_member:
                    cache_manager.set('members', member_key, member)
                    stats['members_added'] += 1

                # 팀이 있는 경우에만 멤버-팀 연결
                if team:
                    team_key = f"room:{room}:team:{team}"
                    cache_manager.set('member_teams', member_key, team)
                    stats['member_team_links'] += 1
                    print(f"[SEED] Member linked: {member} -> {team} (room: {room})")
                else:
                    stats['members_without_team'] += 1
                    print(f"[SEED] Member added without team: {member} (room: {room})")

            except Exception as e:
                error_msg = f"멤버 처리 실패 ({member}): {str(e)}"
                stats['errors'].append(error_msg)
                print(f"[SEED ERROR] {error_msg}")

        # 8. 결과 반환
        success_msg = (
            f"Seed 완료!\n"
            f"- 전체 행: {stats['total_rows']}\n"
            f"- 추가된 팀: {stats['teams_added']}\n"
            f"- 추가된 멤버: {stats['members_added']}\n"
            f"- 멤버-팀 연결: {stats['member_team_links']}\n"
            f"- 팀 없는 멤버: {stats['members_without_team']}"
        )

        if stats['errors']:
            success_msg += f"\n- 오류: {len(stats['errors'])}개"

        print(f"[SEED] {success_msg}")

        return {
            'success': True,
            'message': success_msg,
            'stats': stats
        }

    except Exception as e:
        error_msg = f"Excel 파일 처리 중 오류 발생: {str(e)}"
        print(f"[SEED ERROR] {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }


def clear_all_data(cache_manager) -> dict:
    """
    모든 팀/멤버 데이터를 삭제합니다.

    Args:
        cache_manager: CacheManager 인스턴스

    Returns:
        dict: 삭제 결과
    """
    try:
        print("[SEED] Clearing all data...")

        # MongoDB에서 모든 컬렉션 삭제
        if cache_manager.mongo_db:
            cache_manager.mongo_db['members'].delete_many({})
            cache_manager.mongo_db['teams'].delete_many({})
            cache_manager.mongo_db['member_teams'].delete_many({})
            print("[SEED] MongoDB collections cleared")

        # Redis에서 모든 키 삭제
        if cache_manager.redis:
            # 패턴별로 삭제
            for pattern in ['room:*:member:*', 'room:*:team:*']:
                keys = cache_manager.redis.keys(pattern)
                if keys:
                    cache_manager.redis.delete(*keys)
            print("[SEED] Redis cache cleared")

        return {
            'success': True,
            'message': '모든 데이터가 삭제되었습니다.'
        }

    except Exception as e:
        error_msg = f"데이터 삭제 중 오류 발생: {str(e)}"
        print(f"[SEED ERROR] {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }
