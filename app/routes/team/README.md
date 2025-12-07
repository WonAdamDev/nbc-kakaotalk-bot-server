# Team API Documentation

팀 관리 API 문서입니다.

## Base URL
```
/api/commands/team/
```

---

## 1. 팀 조회 (GET)

팀 정보와 소속 멤버 목록을 조회합니다.

### Endpoint
```
GET /api/commands/team/
```

### Request Parameters (Query String)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| team      | string | Yes      | 팀 이름     |

### Request Example
```
GET /api/commands/team/?room=테스트방&team=블루
```

### Response

#### 성공 (200 OK) - 팀 존재
```json
{
  "success": true,
  "data": {
    "team": "블루",
    "member_count": 3,
    "members": ["홍길동", "김철수", "이영희"],
    "exists": true
  }
}
```

**data 필드:**
- `team` (string): 팀 이름
- `member_count` (number): 팀 소속 멤버 수
- `members` (string[]): 소속 멤버 이름 배열
- `exists` (boolean): 팀 존재 여부 (true)

#### 성공 (200 OK) - 팀 존재, 멤버 없음
```json
{
  "success": true,
  "data": {
    "team": "블루",
    "member_count": 0,
    "members": [],
    "exists": true
  }
}
```

#### 실패 (404 Not Found) - 팀 없음
```json
{
  "success": false,
  "data": {
    "team": "블루",
    "exists": false
  }
}
```

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 2. 팀 생성 (POST)

새로운 팀을 생성합니다.

### Endpoint
```
POST /api/commands/team/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| team      | string | Yes      | 생성할 팀 이름 |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "team": "블루"
}
```

### Response

#### 성공 (200 OK) - 팀 생성 완료
```json
{
  "success": true,
  "data": {
    "team": "블루",
    "created": true
  }
}
```

**data 필드:**
- `team` (string): 생성된 팀 이름
- `created` (boolean): 생성 여부 (true)

#### 실패 (400 Bad Request) - 이미 존재하는 팀
```json
{
  "success": false,
  "data": {
    "team": "블루",
    "created": false,
    "reason": "already_exists"
  }
}
```

**data 필드:**
- `team` (string): 팀 이름
- `created` (boolean): 생성 여부 (false)
- `reason` (string): 실패 사유
  - `already_exists`: 팀이 이미 존재함

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 3. 팀 삭제 (DELETE)

팀을 삭제합니다. 소속 멤버가 있는 경우 삭제할 수 없습니다.

### Endpoint
```
DELETE /api/commands/team/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| team      | string | Yes      | 삭제할 팀 이름 |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "team": "블루"
}
```

### Response

#### 성공 (200 OK) - 팀 삭제 완료
```json
{
  "success": true,
  "data": {
    "team": "블루",
    "deleted": true
  }
}
```

**data 필드:**
- `team` (string): 삭제된 팀 이름
- `deleted` (boolean): 삭제 여부 (true)

#### 실패 (404 Not Found) - 팀이 존재하지 않음
```json
{
  "success": false,
  "data": {
    "team": "블루",
    "deleted": false,
    "reason": "not_found"
  }
}
```

**data 필드:**
- `team` (string): 팀 이름
- `deleted` (boolean): 삭제 여부 (false)
- `reason` (string): 실패 사유
  - `not_found`: 팀이 존재하지 않음

#### 실패 (400 Bad Request) - 소속 멤버가 있음
```json
{
  "success": false,
  "data": {
    "team": "블루",
    "deleted": false,
    "reason": "has_members",
    "member_count": 3
  }
}
```

**data 필드:**
- `team` (string): 팀 이름
- `deleted` (boolean): 삭제 여부 (false)
- `reason` (string): 실패 사유
  - `has_members`: 소속 멤버가 있어 삭제 불가
- `member_count` (number): 소속 멤버 수

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 클라이언트 사용 예시

### 팀 조회
```javascript
// 요청
paramMap = {
  room: room,
  team: "블루"
};
response = sendRequest("/api/commands/team/", paramMap, HttpMethod.GET);

// 응답 (data 객체)
{
  team: "블루",
  member_count: 3,
  members: ["홍길동", "김철수", "이영희"],
  exists: true
}

// 포맷팅
formatTeamGetResponse(response);
// 출력: "블루팀 정보\n멤버 수: 3명\n멤버: 홍길동, 김철수, 이영희"
```

### 팀 생성
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  team: "블루"
};
response = sendRequest("/api/commands/team/", paramMap, HttpMethod.POST);

// 응답 (data 객체) - 성공
{
  team: "블루",
  created: true
}

// 포맷팅
formatTeamPostResponse(response);
// 출력: "블루팀이 생성되었습니다."

// 응답 (data 객체) - 실패 (이미 존재)
{
  team: "블루",
  created: false,
  reason: "already_exists"
}

// 포맷팅
formatTeamPostResponse(response);
// 출력: "블루팀이 이미 존재합니다."
```

### 팀 삭제
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  team: "블루"
};
response = sendRequest("/api/commands/team/", paramMap, HttpMethod.DELETE);

// 응답 (data 객체) - 성공
{
  team: "블루",
  deleted: true
}

// 포맷팅
formatTeamDeleteResponse(response);
// 출력: "블루팀이 삭제되었습니다."

// 응답 (data 객체) - 실패 (멤버 있음)
{
  team: "블루",
  deleted: false,
  reason: "has_members",
  member_count: 3
}

// 포맷팅
formatTeamDeleteResponse(response);
// 출력: "블루팀에 3명의 멤버가 있어 삭제할 수 없습니다."
```

---

## 데이터 구조

### Cache Keys
팀 정보는 Redis 캐시에 다음 형식으로 저장됩니다:

```
room:{room}:team:{team}
```

예시:
```
room:테스트방:team:블루
```

### Cache Namespaces
- `teams`: 팀 정보
- `member_teams`: 멤버-팀 배정 정보 (별도 API 참조)

### 팀 멤버 조회 로직
팀에 소속된 멤버를 조회할 때:
1. `member_teams` 네임스페이스에서 해당 팀 이름으로 모든 키를 검색
2. 키 형식: `room:{room}:member:{member}`
3. 키에서 멤버 이름 추출: `key.split(':')[-1]`

---

## 비즈니스 로직

### 팀 삭제 제약사항
- 팀에 소속된 멤버가 있으면 삭제할 수 없습니다.
- 먼저 모든 멤버의 팀 배정을 해제한 후 팀을 삭제해야 합니다.
- 삭제 시 고아 데이터 방지를 위해 `member_teams`에서 해당 팀 관련 데이터를 정리합니다.

---

## 에러 처리

모든 API는 다음 두 가지 응답 형식을 사용합니다:

1. **성공 시**: `data` 필드에 구조화된 데이터
2. **실패 시**: `message` 필드에 에러 메시지 또는 `data` 필드에 실패 정보

클라이언트는 `success` 필드를 확인하여 성공/실패를 판단할 수 있습니다.
