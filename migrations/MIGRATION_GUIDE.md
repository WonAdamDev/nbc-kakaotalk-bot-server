# 팀/멤버 ID 시스템 마이그레이션 가이드

## 개요

기존 이름 기반 팀/멤버 시스템을 ID 기반 시스템으로 업그레이드합니다.

**목표**:
- 팀에 고유 ID 발급 (`TEAM_X7Y2K9P3`)
- 멤버에 고유 ID 발급 (`MEM_X7Y2K9P3`)
- 경기 출석 선수에 ID 연결 (프리셋 멤버 vs 게스트 구분)
- 향후 통계 기능 구현을 위한 기반 마련

---

## 마이그레이션 순서

### 1단계: PostgreSQL 마이그레이션 (필수)

**목적**: `lineups` 테이블에 member_id 관련 컬럼 추가

```bash
# 데이터베이스 접속 정보 확인
echo $DATABASE_URL
# 또는
cat .env | grep DATABASE_URL

# 마이그레이션 실행
psql <DATABASE_URL> -f migrations/add_member_ids_to_lineups.sql
```

**실행 내용**:
```sql
ALTER TABLE lineups ADD COLUMN IF NOT EXISTS member_id VARCHAR(13);
ALTER TABLE lineups ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE;
ALTER TABLE lineups ADD COLUMN IF NOT EXISTS team_id_snapshot VARCHAR(13);

CREATE INDEX IF NOT EXISTS idx_lineup_member_id ON lineups(member_id);
CREATE INDEX IF NOT EXISTS idx_lineup_is_guest ON lineups(is_guest);
```

**확인**:
```bash
psql <DATABASE_URL> -c "\d lineups"
```

---

### 2단계: MongoDB 마이그레이션 (필수)

**목적**: 기존 팀/멤버 데이터에 ID 발급

```bash
cd nbc-kakaotalk-bot-server

# 환경 변수 설정
export MONGO_URI="mongodb://localhost:27017/"  # 실제 MongoDB URI로 변경
export MONGO_DB_NAME="nbc_basketball"          # 실제 DB 이름으로 변경

# 마이그레이션 실행
python migrations/migrate_teams_members_ids.py
```

**프롬프트**:
```
계속하시겠습니까? (yes/no): yes
```

**실행 결과 예시**:
```
[1/4] 기존 팀 데이터 조회 중...
  → 발견: 5개 팀 (key-value 구조)

[2/4] 팀 데이터 마이그레이션 중...
  ✅ 테스트방/블루 → TEAM_X7Y2K9P3
  ✅ 테스트방/화이트 → TEAM_A1B2C3D4
  ...

  완료: 5개 생성, 0개 건너뜀

[3/4] 기존 멤버 데이터 조회 중...
  → 발견: 15개 멤버 (key-value 구조)

[4/4] 멤버 데이터 마이그레이션 중...
  ✅ 테스트방/김철수 → MEM_E5F6G7H8 (팀: 블루 / TEAM_X7Y2K9P3)
  ✅ 테스트방/이영희 → MEM_I9J0K1L2 (팀: 화이트 / TEAM_A1B2C3D4)
  ...

  완료: 15개 생성, 0개 건너뜀

===========================================================
마이그레이션 완료!
===========================================================
```

**확인**:
```bash
# MongoDB에 접속하여 확인
mongosh <MONGO_URI>

> use nbc_basketball
> db.teams.find().pretty()
{
  "_id": "TEAM_X7Y2K9P3",
  "room_name": "테스트방",
  "name": "블루"
}

> db.members.find().pretty()
{
  "_id": "MEM_E5F6G7H8",
  "room_name": "테스트방",
  "name": "김철수",
  "team_id": "TEAM_X7Y2K9P3"
}
```

---

### 3단계: 서버 재시작 (필수)

수정된 코드를 적용하기 위해 서버를 재시작합니다.

```bash
# 서버 중지
# (Ctrl+C 또는 프로세스 종료)

# 서버 시작
python app.py
# 또는
flask run
```

---

### 4단계: 프론트엔드 테스트 (권장)

**테스트 항목**:

1. **프리셋 멤버 추가**
   - 출석 모달 → "👤 방 멤버 추가" 탭
   - 멤버 선택 후 출석 처리
   - ✅ 멤버 이름 옆에 `#X7Y2` 형식의 ID 표시 확인

2. **게스트 추가**
   - 출석 모달 → "🎭 게스트 추가" 탭
   - 이름 입력 후 출석 처리
   - ✅ 멤버 이름 옆에 `#A1B2 (게스트)` 형식 표시 확인

3. **팀/멤버 생성**
   - 카카오톡 봇에서 팀/멤버 생성
   - ✅ MongoDB에서 ID가 함께 저장되는지 확인

---

## 롤백 (문제 발생 시)

### PostgreSQL 롤백

```sql
-- lineups 테이블에서 추가된 컬럼 제거
ALTER TABLE lineups DROP COLUMN IF EXISTS member_id;
ALTER TABLE lineups DROP COLUMN IF EXISTS is_guest;
ALTER TABLE lineups DROP COLUMN IF EXISTS team_id_snapshot;

-- 인덱스 제거
DROP INDEX IF EXISTS idx_lineup_member_id;
DROP INDEX IF EXISTS idx_lineup_is_guest;
```

### MongoDB 롤백

MongoDB 마이그레이션은 **원본 데이터를 유지**하므로 롤백이 필요하지 않습니다.
- 기존 key-value 구조: 그대로 유지됨
- 새 document 구조: 필요시 수동 삭제

새로 추가된 document만 삭제하려면:
```javascript
// MongoDB shell
db.teams.deleteMany({ _id: { $regex: /^TEAM_/ } })
db.members.deleteMany({ _id: { $regex: /^MEM_/ } })
```

---

## FAQ

### Q1: 마이그레이션 중 기존 데이터가 손실되나요?
**A**: 아니요. 마이그레이션은 **새로운 구조를 추가**하는 방식으로, 기존 데이터는 유지됩니다.
- PostgreSQL: 새 컬럼 추가 (기존 값은 NULL)
- MongoDB: 새 document 추가 (기존 key-value 구조 유지)

### Q2: 마이그레이션 후 기존 경기 데이터는?
**A**: 기존 경기의 라인업은 `member_id`가 NULL입니다. 이는 정상이며, 새로 생성되는 경기부터 ID가 저장됩니다.

### Q3: 팀/멤버를 중복 생성하면?
**A**: MongoDB에서 중복 확인 로직이 있어, 같은 방/같은 이름의 팀/멤버는 기존 ID를 반환합니다.

### Q4: Redis는 어떻게 되나요?
**A**: Redis는 캐시로만 사용됩니다. 영구 저장소는 MongoDB이므로, Redis 데이터 손실은 문제없습니다.
- 서버 시작 시 MongoDB → Redis로 자동 로드됨
- 기존 Redis key-value 구조도 하위 호환성을 위해 유지됨

### Q5: 마이그레이션 실패 시 재실행 가능한가요?
**A**: 네. 마이그레이션 스크립트는 **멱등성(idempotent)**을 보장합니다.
- 이미 존재하는 팀/멤버는 건너뜀
- 여러 번 실행해도 안전함

---

## 트러블슈팅

### 문제 1: PostgreSQL 연결 실패
```
psql: could not connect to server
```

**해결**:
```bash
# DATABASE_URL 환경 변수 확인
echo $DATABASE_URL

# 직접 연결 정보 입력
psql -h localhost -U your_user -d your_database -f migrations/add_member_ids_to_lineups.sql
```

### 문제 2: MongoDB 연결 실패
```
pymongo.errors.ServerSelectionTimeoutError
```

**해결**:
```bash
# MongoDB가 실행 중인지 확인
mongosh --eval "db.adminCommand('ping')"

# MONGO_URI 확인
echo $MONGO_URI
```

### 문제 3: Python 모듈 없음
```
ModuleNotFoundError: No module named 'pymongo'
```

**해결**:
```bash
pip install pymongo
# 또는
pip install -r requirements.txt
```

---

## 문의

마이그레이션 중 문제가 발생하면:
1. 에러 로그 전체 복사
2. MongoDB/PostgreSQL 버전 확인
3. 개발팀에 문의
