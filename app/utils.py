"""
유틸리티 함수 모음
"""
import uuid
from datetime import datetime


def generate_id(prefix):
    """
    고유 ID 생성

    Args:
        prefix: ID 접두사 (TEAM, MEM, GUEST 등)

    Returns:
        형식: {prefix}_{8자리 UUID}
        예: TEAM_X7Y2K9P3, MEM_A1B2C3D4
    """
    return f"{prefix}_{str(uuid.uuid4())[:8].upper()}"


def generate_team_id():
    """팀 ID 생성"""
    return generate_id('TEAM')


def generate_member_id():
    """멤버 ID 생성"""
    return generate_id('MEM')


def generate_guest_id():
    """게스트 ID 생성"""
    return generate_id('GUEST')
