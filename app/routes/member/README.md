# Member API Documentation

멤버 관리 API 문서입니다.

## Base URL
```
/api/commands/member/
```

---

## 1. 멤버 조회 (GET)

멤버 정보를 조회합니다.

### Endpoint
```
GET /api/commands/member/
```

### Request Parameters (Query String)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| member    | string | Yes      | 멤버 이름   |

### Request Example
```
GET /api/commands/member/?room=테스트방&member=홍길동
```

### Response

#### 성공 (200 OK) - 멤버 존재
```json
{
  "success": true,
  "data": {
    "member": "홍길동",
    "team": "블루",
    "exists": true
  }
}
```

**data 필드:**
- `member` (string): 멤버 이름
- `team` (string | null): 배정된 팀 이름 (배정되지 않은 경우 null)
- `exists` (boolean): 멤버 존재 여부 (true)

#### 실패 (404 Not Found) - 멤버 없음
```json
{
  "success": false,
  "data": {
    "member": "홍길동",
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

## 2. 멤버 생성 (POST)

새로운 멤버를 생성합니다.

### Endpoint
```
POST /api/commands/member/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| member    | string | Yes      | 생성할 멤버 이름 |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "member": "홍길동"
}
```

### Response

#### 성공 (200 OK)
```json
{
  "success": true,
  "data": {
    "member": "홍길동"
  }
}
```

**data 필드:**
- `member` (string): 생성된 멤버 이름

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 3. 멤버 삭제 (DELETE)

멤버를 삭제합니다. 팀 배정 정보도 함께 삭제됩니다.

### Endpoint
```
DELETE /api/commands/member/
```

### Request Body (JSON)
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| room      | string | Yes      | 방 이름     |
| sender    | string | Yes      | 요청자 이름 |
| member    | string | Yes      | 삭제할 멤버 이름 |

### Request Example
```json
{
  "room": "테스트방",
  "sender": "관리자",
  "member": "홍길동"
}
```

### Response

#### 성공 (200 OK)
```json
{
  "success": true,
  "data": {
    "member": "홍길동"
  }
}
```

**data 필드:**
- `member` (string): 삭제된 멤버 이름

#### 에러 (500 Internal Server Error)
```json
{
  "success": false,
  "message": "오류가 발생했습니다: {에러 메시지}"
}
```

---

## 클라이언트 사용 예시

### 멤버 조회
```javascript
// 요청
paramMap = {
  room: room,
  member: "홍길동"
};
response = sendRequest("/api/commands/member/", paramMap, HttpMethod.GET);

// 응답 (data 객체)
{
  member: "홍길동",
  team: "블루",
  exists: true
}

// 포맷팅
formatMemberGetResponse(response);
// 출력: "홍길동님 정보\n팀: 블루"
```

### 멤버 생성
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  member: "홍길동"
};
response = sendRequest("/api/commands/member/", paramMap, HttpMethod.POST);

// 응답 (data 객체)
{
  member: "홍길동"
}

// 포맷팅
formatMemberPostResponse(response);
// 출력: "홍길동님이 멤버가 되었습니다."
```

### 멤버 삭제
```javascript
// 요청
paramMap = {
  sender: sender,
  room: room,
  member: "홍길동"
};
response = sendRequest("/api/commands/member/", paramMap, HttpMethod.DELETE);

// 응답 (data 객체)
{
  member: "홍길동"
}

// 포맷팅
formatMemberDeleteResponse(response);
// 출력: "홍길동님이 멤버에서 제거되었습니다."
```

---

## 데이터 구조

### Cache Keys
멤버 정보는 Redis 캐시에 다음 형식으로 저장됩니다:

```
room:{room}:member:{member}
```

예시:
```
room:테스트방:member:홍길동
```

### Cache Namespaces
- `members`: 멤버 정보
- `member_teams`: 멤버-팀 배정 정보 (별도 API 참조)

---

## 에러 처리

모든 API는 다음 두 가지 응답 형식을 사용합니다:

1. **성공 시**: `data` 필드에 구조화된 데이터
2. **실패 시**: `message` 필드에 에러 메시지

클라이언트는 `success` 필드를 확인하여 성공/실패를 판단할 수 있습니다.
