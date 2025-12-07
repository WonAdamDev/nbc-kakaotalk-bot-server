# 경기 관리 API

PostgreSQL 기반 농구 경기 관리 API입니다.

## 데이터 구조

### Game (경기)
- `game_id`: 8자리 고유 ID (예: ABC12345)
- `room`: 카카오톡 방 이름
- `creator`: 경기 생성자
- `date`: 경기 날짜
- `status`: 준비중 | 진행중 | 종료
- `current_quarter`: 현재 쿼터 번호
- `final_score_blue`: 블루팀 최종 점수
- `final_score_white`: 화이트팀 최종 점수
- `winner`: 블루 | 화이트 | 무승부

### Lineup (순번)
- `team`: 블루 | 화이트
- `member`: 선수 이름
- `number`: 도착 순번
- `arrived`: 도착 여부
- `arrived_at`: 도착 시각

### Quarter (쿼터)
- `quarter_number`: 쿼터 번호
- `status`: 진행중 | 종료
- `playing_blue`: 블루팀 출전 선수 번호 배열 [1,2,3,4,5]
- `playing_white`: 화이트팀 출전 선수 번호 배열
- `bench_blue`: 블루팀 벤치 선수 번호 배열
- `bench_white`: 화이트팀 벤치 선수 번호 배열
- `score_blue`: 블루팀 쿼터 점수
- `score_white`: 화이트팀 쿼터 점수

---

## 1. 경기 생성

```
POST /api/game/create
```

### Request Body
```json
{
  "room": "NBC 농구동호회",
  "creator": "홍길동",
  "date": "2024-01-25"  // optional, 기본값: 오늘
}
```

### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "game_id": "ABC12345",
    "url": "https://your-frontend-url.com/game/ABC12345",
    "game": {
      "game_id": "ABC12345",
      "room": "NBC 농구동호회",
      "creator": "홍길동",
      "date": "2024-01-25",
      "created_at": "2024-01-25T10:00:00",
      "status": "준비중",
      "current_quarter": 0,
      "final_score": null,
      "winner": null
    }
  }
}
```

---

## 2. 경기 조회

```
GET /api/game/<game_id>
```

### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "game": {
      "game_id": "ABC12345",
      "room": "NBC 농구동호회",
      "status": "진행중",
      "current_quarter": 2,
      ...
    },
    "lineups": {
      "블루": [
        {
          "team": "블루",
          "member": "홍길동",
          "number": 1,
          "arrived": true,
          "arrived_at": "2024-01-25T10:05:00"
        },
        ...
      ],
      "화이트": [...]
    },
    "quarters": [
      {
        "quarter": 1,
        "status": "종료",
        "playing": {
          "blue": [1, 2, 3, 4, 5],
          "white": [1, 2, 3, 4, 5]
        },
        "bench": {
          "blue": [6, 7],
          "white": [6, 7]
        },
        "score": {
          "blue": 12,
          "white": 10
        },
        "started_at": "2024-01-25T10:10:00",
        "ended_at": "2024-01-25T10:25:00"
      },
      ...
    ]
  }
}
```

---

## 3. 경기 시작

```
POST /api/game/<game_id>/start
```

### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "game_id": "ABC12345",
    "status": "진행중",
    "started_at": "2024-01-25T10:10:00",
    ...
  }
}
```

### 에러 (400 Bad Request)
```json
{
  "success": false,
  "error": "Game is already 진행중"
}
```

---

## 4. 경기 종료

```
POST /api/game/<game_id>/end
```

### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "game_id": "ABC12345",
    "status": "종료",
    "ended_at": "2024-01-25T11:30:00",
    "final_score": {
      "blue": 45,
      "white": 42
    },
    "winner": "블루"
  }
}
```

**주의**: 모든 쿼터의 점수를 자동으로 합산하여 최종 점수 계산

---

## 5. 경기 삭제

```
DELETE /api/game/<game_id>
```

### Response (200 OK)
```json
{
  "success": true,
  "message": "Game deleted successfully"
}
```

**주의**: CASCADE DELETE로 연관된 라인업과 쿼터 데이터도 모두 삭제됨

---

## 6. 선수 도착 처리

```
POST /api/game/<game_id>/lineup/arrival
```

### Request Body
```json
{
  "team": "블루",
  "member": "홍길동"
}
```

### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "team": "블루",
    "member": "홍길동",
    "number": 1,
    "arrived": true,
    "arrived_at": "2024-01-25T10:05:00"
  }
}
```

**주의**: 도착 순서대로 자동으로 번호 부여 (1, 2, 3, ...)

---

## 7. 선수 제거

```
DELETE /api/game/<game_id>/lineup/<lineup_id>
```

### Response (200 OK)
```json
{
  "success": true,
  "message": "Player removed successfully"
}
```

**주의**: 제거 후 뒤의 번호들이 자동으로 재정렬됨

---

## 8. 쿼터 시작 (자동 로테이션)

```
POST /api/game/<game_id>/quarter/start
```

### Request Body (optional)
```json
{
  "quarter_number": 2  // optional, 기본값: 현재 쿼터 + 1
}
```

### Response (201 Created)
```json
{
  "success": true,
  "data": {
    "quarter": 1,
    "status": "진행중",
    "playing": {
      "blue": [1, 2, 3, 4, 5],
      "white": [1, 2, 3, 4, 5]
    },
    "bench": {
      "blue": [6, 7],
      "white": [6, 7]
    },
    "score": {
      "blue": 0,
      "white": 0
    },
    "started_at": "2024-01-25T10:10:00"
  }
}
```

### 로테이션 로직

#### 첫 쿼터 (Q1)
- 순번 1-5번: 출전
- 순번 6번 이후: 벤치

#### 두 번째 쿼터 이후 (Q2, Q3, ...)
1. 이전 쿼터의 벤치 선수들이 **역순**으로 먼저 출전
2. 남은 자리는 이전 쿼터 출전 선수들로 채움

**예시:**
```
Q1 출전: [1,2,3,4,5], 벤치: [6,7,8]
Q2 출전: [8,7,6,1,2], 벤치: [3,4,5]
Q3 출전: [5,4,3,8,7], 벤치: [6,1,2]
```

### 에러
```json
{
  "success": false,
  "error": "Each team needs at least 5 players"
}
```

---

## 9. 쿼터 종료

```
POST /api/game/<game_id>/quarter/<quarter_number>/end
```

### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "quarter": 1,
    "status": "종료",
    "ended_at": "2024-01-25T10:25:00",
    ...
  }
}
```

---

## 10. 쿼터 점수 업데이트

```
PUT /api/game/<game_id>/quarter/<quarter_number>/score
```

### Request Body
```json
{
  "score_blue": 12,
  "score_white": 10
}
```

### Response (200 OK)
```json
{
  "success": true,
  "data": {
    "quarter": 1,
    "score": {
      "blue": 12,
      "white": 10
    },
    ...
  }
}
```

---

## WebSocket 이벤트

클라이언트는 Socket.io를 통해 실시간 업데이트를 받을 수 있습니다.

### 연결
```javascript
import io from 'socket.io-client';

const socket = io('https://your-server-url.com');

socket.on('connected', (data) => {
  console.log(data.message); // "Connected to game server"
});
```

### 경기 방 참여
```javascript
socket.emit('join_game', { game_id: 'ABC12345' });

socket.on('joined_game', (data) => {
  console.log(data.message); // "Joined game ABC12345"
});
```

### 게임 업데이트 수신
```javascript
socket.on('game_update', (data) => {
  console.log(data.type); // 'game_started', 'player_arrived', 'quarter_started', etc.
  console.log(data.data); // 업데이트된 데이터
});
```

#### 업데이트 이벤트 타입
- `game_started`: 경기 시작
- `game_ended`: 경기 종료
- `game_deleted`: 경기 삭제
- `player_arrived`: 선수 도착
- `player_removed`: 선수 제거
- `quarter_started`: 쿼터 시작
- `quarter_ended`: 쿼터 종료
- `score_updated`: 점수 업데이트

### 현재 게임 상태 요청
```javascript
socket.emit('request_game_state', { game_id: 'ABC12345' });

socket.on('game_state', (data) => {
  console.log(data.game);     // 경기 정보
  console.log(data.lineups);  // 라인업 정보
  console.log(data.quarters); // 쿼터 정보
});
```

### 경기 방 나가기
```javascript
socket.emit('leave_game', { game_id: 'ABC12345' });

socket.on('left_game', (data) => {
  console.log(data.message); // "Left game ABC12345"
});
```

---

## 데이터베이스 스키마

### games 테이블
```sql
CREATE TABLE games (
    game_id VARCHAR(8) PRIMARY KEY,
    room VARCHAR(100) NOT NULL,
    creator VARCHAR(50),
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(20) DEFAULT '준비중',
    current_quarter INTEGER DEFAULT 0,
    final_score_blue INTEGER,
    final_score_white INTEGER,
    winner VARCHAR(10)
);
```

### lineups 테이블
```sql
CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(8) REFERENCES games(game_id) ON DELETE CASCADE,
    team VARCHAR(10) NOT NULL,
    member VARCHAR(50) NOT NULL,
    number INTEGER NOT NULL,
    arrived BOOLEAN DEFAULT TRUE,
    arrived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(game_id, team, number)
);

CREATE INDEX idx_lineup_game_team ON lineups(game_id, team);
```

### quarters 테이블
```sql
CREATE TABLE quarters (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(8) REFERENCES games(game_id) ON DELETE CASCADE,
    quarter_number INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT '진행중',
    playing_blue JSON,
    playing_white JSON,
    bench_blue JSON,
    bench_white JSON,
    score_blue INTEGER DEFAULT 0,
    score_white INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    UNIQUE(game_id, quarter_number)
);

CREATE INDEX idx_quarter_game ON quarters(game_id);
```

---

## 에러 응답 형식

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "success": false,
  "error": "에러 메시지"
}
```

### HTTP 상태 코드
- `200 OK`: 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스를 찾을 수 없음
- `500 Internal Server Error`: 서버 에러

---

## 환경 변수

Railway 배포 시 다음 환경 변수를 설정하세요:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here
DEBUG=False
```

로컬 개발 시 SQLite를 기본으로 사용합니다 (`sqlite:///basketball_games.db`).
