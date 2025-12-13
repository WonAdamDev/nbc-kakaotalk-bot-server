-- rooms 테이블 생성
CREATE TABLE IF NOT EXISTS rooms (
    room_id VARCHAR(8) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기존 게임의 room 데이터를 기반으로 rooms 레코드 생성
INSERT INTO rooms (room_id, name, created_at)
SELECT
    UPPER(SUBSTRING(MD5(room)::text, 1, 8)) as room_id,
    room as name,
    MIN(created_at) as created_at
FROM games
WHERE room IS NOT NULL AND room != ''
GROUP BY room
ON CONFLICT (name) DO NOTHING;

-- games 테이블에 room_id 컬럼 추가
ALTER TABLE games
ADD COLUMN IF NOT EXISTS room_id VARCHAR(8);

-- 기존 games의 room을 room_id로 매핑
UPDATE games g
SET room_id = r.room_id
FROM rooms r
WHERE g.room = r.name;

-- room_id를 NOT NULL로 변경하고 외래키 추가
ALTER TABLE games
ALTER COLUMN room_id SET NOT NULL,
ADD CONSTRAINT fk_games_room_id
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE;

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_games_room_id ON games(room_id);

-- 기존 room 컬럼은 일단 유지 (호환성을 위해, 나중에 제거 가능)
-- ALTER TABLE games DROP COLUMN room;
