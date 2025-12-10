"""
PostgreSQL 데이터 모델 (경기 데이터)
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Game(db.Model):
    """경기 정보"""
    __tablename__ = 'games'

    game_id = db.Column(db.String(8), primary_key=True)
    room = db.Column(db.String(100), nullable=False)
    creator = db.Column(db.String(50))
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='준비중')  # 준비중, 진행중, 종료
    current_quarter = db.Column(db.Integer, default=0)
    final_score_blue = db.Column(db.Integer)
    final_score_white = db.Column(db.Integer)
    winner = db.Column(db.String(10))  # 블루, 화이트, 무승부

    # 관계 (CASCADE DELETE)
    lineups = db.relationship('Lineup', backref='game', cascade='all, delete-orphan', lazy=True)
    quarters = db.relationship('Quarter', backref='game', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'game_id': self.game_id,
            'room': self.room,
            'creator': self.creator,
            'date': self.date.isoformat() if self.date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'status': self.status,
            'current_quarter': self.current_quarter,
            'final_score': {
                'blue': self.final_score_blue,
                'white': self.final_score_white
            } if self.final_score_blue is not None else None,
            'winner': self.winner
        }


class Lineup(db.Model):
    """순번 정보"""
    __tablename__ = 'lineups'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(8), db.ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False)
    team = db.Column(db.String(10), nullable=False)  # 블루, 화이트
    member = db.Column(db.String(50), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    arrived = db.Column(db.Boolean, default=True)
    arrived_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('game_id', 'team', 'number', name='unique_lineup'),
        db.Index('idx_lineup_game_team', 'game_id', 'team'),
    )

    def to_dict(self):
        """딕셔너리 변환"""
        return {
            'team': self.team,
            'member': self.member,
            'number': self.number,
            'arrived': self.arrived,
            'arrived_at': self.arrived_at.isoformat() if self.arrived_at else None
        }


class Quarter(db.Model):
    """쿼터 정보"""
    __tablename__ = 'quarters'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(8), db.ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False)
    quarter_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='진행중')  # 진행중, 종료
    playing_blue = db.Column(db.JSON)  # [1, 2, 3, 4, 5]
    playing_white = db.Column(db.JSON)
    bench_blue = db.Column(db.JSON)  # [6, 7]
    bench_white = db.Column(db.JSON)
    lineup_snapshot = db.Column(db.JSON)  # {'블루': {1: '홍길동', 2: '김철수'}, '화이트': {...}}
    score_blue = db.Column(db.Integer, default=0)
    score_white = db.Column(db.Integer, default=0)
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
                'blue': self.playing_blue or [],
                'white': self.playing_white or []
            },
            'bench': {
                'blue': self.bench_blue or [],
                'white': self.bench_white or []
            },
            'lineup_snapshot': self.lineup_snapshot or {},
            'score': {
                'blue': self.score_blue,
                'white': self.score_white
            },
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }
