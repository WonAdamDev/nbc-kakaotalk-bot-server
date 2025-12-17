"""
PostgreSQL 데이터 모델 (경기 데이터)
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Room(db.Model):
    """방 정보"""
    __tablename__ = 'rooms'

    room_id = db.Column(db.String(8), primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계
    teams = db.relationship('Team', backref='room', cascade='all, delete-orphan', lazy=True)
    members = db.relationship('Member', backref='room', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'room_id': self.room_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class Team(db.Model):
    """팀 정보"""
    __tablename__ = 'teams'

    team_id = db.Column(db.String(13), primary_key=True)  # TEAM_XXXXXXXX
    room_id = db.Column(db.String(8), db.ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관계
    members = db.relationship('Member', backref='team', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('room_id', 'name', name='unique_team_per_room'),
        db.Index('idx_team_room', 'room_id'),
    )

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'team_id': self.team_id,
            'room_id': self.room_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class Member(db.Model):
    """멤버 정보"""
    __tablename__ = 'members'

    member_id = db.Column(db.String(13), primary_key=True)  # MEM_XXXXXXXX
    room_id = db.Column(db.String(8), db.ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.String(13), db.ForeignKey('teams.team_id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_member_room', 'room_id'),
        db.Index('idx_member_team', 'team_id'),
        db.Index('idx_member_room_name', 'room_id', 'name'),
    )

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'member_id': self.member_id,
            'room_id': self.room_id,
            'name': self.name,
            'team_id': self.team_id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class Game(db.Model):
    """경기 정보"""
    __tablename__ = 'games'

    game_id = db.Column(db.String(8), primary_key=True)
    room_id = db.Column(db.String(8), db.ForeignKey('rooms.room_id', ondelete='CASCADE'), nullable=False)
    room = db.Column(db.String(100), nullable=False)  # 호환성 유지용 (deprecated)
    alias = db.Column(db.String(100), nullable=False)  # 경기 별칭 (기본값: date)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='준비중')  # 준비중, 진행중, 종료
    current_quarter = db.Column(db.Integer, default=0)
    team_home = db.Column(db.String(50))  # 홈팀으로 경기하는 실제 팀 이름
    team_away = db.Column(db.String(50))  # 어웨이팀으로 경기하는 실제 팀 이름
    final_score_home = db.Column(db.Integer)
    final_score_away = db.Column(db.Integer)
    winner = db.Column(db.String(10))  # home, away, 무승부
    parent_game_id = db.Column(db.String(8), db.ForeignKey('games.game_id', ondelete='SET NULL'), nullable=True)  # 이어하기 시 원본 경기

    # 관계 (CASCADE DELETE)
    lineups = db.relationship('Lineup', backref='game', cascade='all, delete-orphan', lazy=True)
    quarters = db.relationship('Quarter', backref='game', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'game_id': self.game_id,
            'room_id': self.room_id,
            'room': self.room,
            'alias': self.alias,
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'started_at': self.started_at.isoformat() + 'Z' if self.started_at else None,
            'ended_at': self.ended_at.isoformat() + 'Z' if self.ended_at else None,
            'status': self.status,
            'current_quarter': self.current_quarter,
            'team_home': self.team_home,
            'team_away': self.team_away,
            'final_score': {
                'home': self.final_score_home,
                'away': self.final_score_away
            } if self.final_score_home is not None else None,
            'winner': self.winner,
            'parent_game_id': self.parent_game_id
        }


class Lineup(db.Model):
    """순번 정보"""
    __tablename__ = 'lineups'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(8), db.ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False)

    # 선수 식별 (새로 추가)
    member_id = db.Column(db.String(13), nullable=True)  # MEM_X7Y2K9P3 또는 GST_X7Y2K9P3
    is_guest = db.Column(db.Boolean, default=False)

    # 경기 당시 스냅샷 (새로 추가)
    team_id_snapshot = db.Column(db.String(13), nullable=True)  # TEAM_X7Y2K9P3

    # 기존 필드
    team = db.Column(db.String(10), nullable=False)  # home, away
    member = db.Column(db.String(50), nullable=False)  # 이름 (표시용)
    number = db.Column(db.Integer, nullable=False)
    arrived = db.Column(db.Boolean, default=True)
    arrived_at = db.Column(db.DateTime, default=datetime.utcnow)
    playing_status = db.Column(db.String(10), default='playing')  # playing, bench

    __table_args__ = (
        db.UniqueConstraint('game_id', 'team', 'number', name='unique_lineup'),
        db.Index('idx_lineup_game_team', 'game_id', 'team'),
    )

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'id': self.id,
            'member_id': self.member_id,
            'is_guest': self.is_guest,
            'team': self.team,
            'member': self.member,
            'number': self.number,
            'arrived': self.arrived,
            'arrived_at': self.arrived_at.isoformat() + 'Z' if self.arrived_at else None,
            'playing_status': self.playing_status or 'playing'
        }


class Quarter(db.Model):
    """쿼터 정보"""
    __tablename__ = 'quarters'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(8), db.ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False)
    quarter_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='진행중')  # 진행중, 종료
    playing_home = db.Column(db.JSON)  # [1, 2, 3, 4, 5]
    playing_away = db.Column(db.JSON)
    bench_home = db.Column(db.JSON)  # [6, 7]
    bench_away = db.Column(db.JSON)
    lineup_snapshot = db.Column(db.JSON)  # {'home': {1: '홍길동', 2: '김철수'}, 'away': {...}}
    score_home = db.Column(db.Integer, default=0)
    score_away = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    __table_args__ = (
        db.UniqueConstraint('game_id', 'quarter_number', name='unique_quarter'),
        db.Index('idx_quarter_game', 'game_id'),
    )

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'quarter': self.quarter_number,
            'status': self.status,
            'playing': {
                'home': self.playing_home or [],
                'away': self.playing_away or []
            },
            'bench': {
                'home': self.bench_home or [],
                'away': self.bench_away or []
            },
            'lineup_snapshot': self.lineup_snapshot or {},
            'score': {
                'home': self.score_home,
                'away': self.score_away
            },
            'started_at': self.started_at.isoformat() + 'Z' if self.started_at else None,
            'ended_at': self.ended_at.isoformat() + 'Z' if self.ended_at else None
        }
