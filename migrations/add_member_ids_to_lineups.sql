-- lineups 테이블에 member_id 관련 컬럼 추가

-- member_id 컬럼 추가 (MEM_X7Y2K9P3 또는 GUEST_X7Y2K9P3)
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS member_id VARCHAR(13);

-- is_guest 컬럼 추가
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE;

-- team_id_snapshot 컬럼 추가 (경기 당시 팀 ID)
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS team_id_snapshot VARCHAR(13);

-- 인덱스 추가 (통계 쿼리 최적화)
CREATE INDEX IF NOT EXISTS idx_lineup_member_id ON lineups(member_id);
CREATE INDEX IF NOT EXISTS idx_lineup_is_guest ON lineups(is_guest);

-- 기존 데이터는 member_id가 NULL (레거시 데이터)
-- is_guest는 FALSE로 유지 (기존 데이터는 모두 멤버로 간주)

COMMENT ON COLUMN lineups.member_id IS '선수 ID (MEM_xxx: 방 멤버, GUEST_xxx: 게스트)';
COMMENT ON COLUMN lineups.is_guest IS '게스트 여부 (통계 제외용)';
COMMENT ON COLUMN lineups.team_id_snapshot IS '경기 당시 소속 팀 ID (스냅샷)';
