# Member-Team API Documentation

멤버-팀 배정 관리 API 문서입니다.

## Base URL
```
/api/commands/member_team/
```

---

## 1. 팀 배정 조회 (GET)

멤버의 팀 배정 정보를 조회합니다.

### Endpoint
```
GET /api/commands/member_team/
```

### Request Parameters (Query String)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| member    | string | Yes      | 멤버 이름   |

### Request Example
```
GET /api/commands/member_team/?room=테스트방&member=홍길동
```

### Response

#### 성공 (200 OK) - 팀에 배정됨
```json
{
  "success": true,
  "data": {
    "member": "홍길동",
    "team": "블루",
    "is_member": true
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `team` (string | null): 배정된 팀 이름 (배정되지 않은 경우 null)
- `is_member` (boolean): 멤버 존재 여부 (true)

#### 성공 (200 OK) - 팀에 배정되지 않음
```json
{
  "success": true,
  "data": {
    "member": "홍길동",
    "team": null,
    "is_member": true
  }
}
```

#### 실패 (404 Not Found) - 멤버가 아님
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
    "is_member": false
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

## 2. 팀 배정 (POST)

멤버를 팀에 배정합니다.

### Endpoint
```
POST /api/commands/member_team/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| member    | string | Yes      | 멤버 이름   |
| team      | string | Yes      | 팀 이름     |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "member": "홍길동",
  "team": "블루"
}
```

### Response

#### 성공 (200 OK) - 배정 완료
```json
{
  "success": true,
  "data": {
    "member": "홍길동",
    "team": "블루",
    "assigned": true
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `team` (string): 배정된 팀 이름
- `assigned` (boolean): 배정 여부 (true)

#### 실패 (404 Not Found) - 멤버를 찾을 수 없음
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
    "team": "블루",
    "assigned": false,
    "reason": "member_not_found"
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `team` (string): 팀 이름
- `assigned` (boolean): 배정 여부 (false)
- `reason` (string): 실패 사유
  - `member_not_found`: 멤버가 존재하지 않음

#### 실패 (404 Not Found) - 팀을 찾을 수 없음
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
    "team": "블루",
    "assigned": false,
    "reason": "team_not_found"
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `team` (string): 팀 이름
- `assigned` (boolean): 배정 여부 (false)
- `reason` (string): 실패 사유
  - `team_not_found`: 팀이 존재하지 않음

#### 실패 (400 Bad Request) - 팀 이름 누락
```json
{
  "success": false,
  "message": "팀 이름을 입력해주세요."
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

## 3. 팀 배정 해제 (DELETE)

멤버의 팀 배정을 해제합니다.

### Endpoint
```
DELETE /api/commands/member_team/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| member    | string | Yes      | 멤버 이름   |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "member": "홍길동"
}
```

### Response

#### 성공 (200 OK) - 배정 해제 완료
```json
{
  "success": true,
  "data": {
    "member": "홍길동",
    "previous_team": "블루",
    "unassigned": true
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `previous_team` (string): 이전에 배정되었던 팀 이름
- `unassigned` (boolean): 해제 여부 (true)

#### 실패 (404 Not Found) - 멤버를 찾을 수 없음
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
    "unassigned": false,
    "reason": "member_not_found"
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `unassigned` (boolean): 해제 여부 (false)
- `reason` (string): 실패 사유
  - `member_not_found`: 멤버가 존재하지 않음

#### 실패 (400 Bad Request) - 팀에 배정되지 않음
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
    "unassigned": false,
    "reason": "no_team_assigned"
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `unassigned` (boolean): 해제 여부 (false)
- `reason` (string): 실패 사유
  - `no_team_assigned`: 팀에 배정되어 있지 않음

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 클라이언트 사용 예시

### 팀 배정 조회
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  member: "홍길동"
};
response = sendRequest("/api/commands/member_team/", paramMap, HttpMethod.GET);

// 응답 (data 객체) - 배정됨
{
  member: "홍길동",
  team: "블루",
  is_member: true
}

// 포맷팅
formatMemberTeamGetResponse(response);
// 출력: "홍길동님은 블루팀에 배정되어 있습니다."

// 응답 (data 객체) - 배정 안됨
{
  member: "홍길동",
  team: null,
  is_member: true
}

// 포맷팅
formatMemberTeamGetResponse(response);
// 출력: "홍길동님은 팀에 배정되어 있지 않습니다."
```

### 팀 배정
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  member: "홍길동",
  team: "블루"
};
response = sendRequest("/api/commands/member_team/", paramMap, HttpMethod.POST);

// 응답 (data 객체) - 성공
{
  member: "홍길동",
  team: "블루",
  assigned: true
}

// 포맷팅
formatMemberTeamPostResponse(response);
// 출력: "홍길동님이 블루팀에 배정되었습니다."

// 응답 (data 객체) - 실패 (멤버 없음)
{
  member: "홍길동",
  team: "블루",
  assigned: false,
  reason: "member_not_found"
}

// 포맷팅
formatMemberTeamPostResponse(response);
// 출력: "홍길동님은 멤버가 아닙니다."

// 응답 (data 객체) - 실패 (팀 없음)
{
  member: "홍길동",
  team: "블루",
  assigned: false,
  reason: "team_not_found"
}

// 포맷팅
formatMemberTeamPostResponse(response);
// 출력: "블루팀은 존재하지 않습니다."
```

### 팀 배정 해제
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  member: "홍길동"
};
response = sendRequest("/api/commands/member_team/", paramMap, HttpMethod.DELETE);

// 응답 (data 객체) - 성공
{
  member: "홍길동",
  previous_team: "블루",
  unassigned: true
}

// 포맷팅
formatMemberTeamDeleteResponse(response);
// 출력: "홍길동님의 팀 배정(블루)이 해제되었습니다."

// 응답 (data 객체) - 실패 (팀 배정 없음)
{
  member: "홍길동",
  unassigned: false,
  reason: "no_team_assigned"
}

// 포맷팅
formatMemberTeamDeleteResponse(response);
// 출력: "홍길동님은 팀에 배정되어 있지 않습니다."
```

---

## 데이터 구조

### Cache Keys
멤버-팀 배정 정보는 Redis 캐시에 다음 형식으로 저장됩니다:

```
room:{room}:member:{member}
```

예시:
```
room:테스트방:member:홍길동
```

### Cache Namespaces
- `member_teams`: 멤버-팀 배정 정보
  - Key: `room:{room}:member:{member}`
  - Value: 팀 이름 (string)

### 관련 데이터
- `members`: 멤버 정보 (Member API 참조)
- `teams`: 팀 정보 (Team API 참조)

---

## 비즈니스 로직

### 팀 배정 제약사항
1. **멤버 존재 확인**: 배정하려는 멤버가 반드시 존재해야 합니다.
2. **팀 존재 확인**: 배정하려는 팀이 반드시 존재해야 합니다.
3. **중복 배정**: 이미 다른 팀에 배정된 멤버를 다른 팀에 배정하면 기존 배정이 덮어씌워집니다.

### 팀 배정 해제 제약사항
1. **멤버 존재 확인**: 멤버가 존재하지 않으면 해제할 수 없습니다.
2. **배정 확인**: 팀에 배정되지 않은 멤버는 해제할 수 없습니다.

### 멤버 삭제 시 동작
멤버가 삭제되면 `member_teams`의 해당 멤버 데이터도 함께 삭제됩니다 (Member API 참조).

---

## 워크플로우 예시

### 멤버를 팀에 배정하는 전체 과정

1. **멤버 생성**
   ```javascript
   POST /api/commands/member/
   { "room": "테스트방", "member": "홍길동" }
   ```

2. **팀 생성**
   ```javascript
   POST /api/commands/team/
   { "room": "테스트방", "team": "블루" }
   ```

3. **멤버를 팀에 배정**
   ```javascript
   POST /api/commands/member_team/
   { "room": "테스트방", "member": "홍길동", "team": "블루" }
   ```

4. **배정 확인**
   ```javascript
   GET /api/commands/member_team/?room=테스트방&member=홍길동
   // 응답: { member: "홍길동", team: "블루", is_member: true }
   ```

---

## 에러 처리

모든 API는 다음 두 가지 응답 형식을 사용합니다:

1. **성공 시**: `data` 필드에 구조화된 데이터
2. **실패 시**: `message` 필드에 에러 메시지 또는 `data` 필드에 실패 정보

클라이언트는 `success` 필드를 확인하여 성공/실패를 판단할 수 있습니다.

---

## 참고 사항

- 멤버는 한 번에 하나의 팀에만 배정될 수 있습니다.
- 팀 배정 시 기존 배정이 있으면 자동으로 덮어씌워집니다.
- 멤버 삭제 시 팀 배정 정보도 함께 삭제됩니다.
- 팀 조회 시 해당 팀에 배정된 모든 멤버 목록을 확인할 수 있습니다 (Team API 참조).
