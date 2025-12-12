-- Migration: Add team_home and team_away fields to games table
-- Date: 2024-12-12
-- Description: Adds team selection fields for tracking which teams are playing

-- Add team_home column
ALTER TABLE games ADD COLUMN IF NOT EXISTS team_home VARCHAR(50);

-- Add team_away column
ALTER TABLE games ADD COLUMN IF NOT EXISTS team_away VARCHAR(50);

-- Add comments for documentation
COMMENT ON COLUMN games.team_home IS '홈팀으로 경기하는 실제 팀 이름 (블루팀)';
COMMENT ON COLUMN games.team_away IS '어웨이팀으로 경기하는 실제 팀 이름 (화이트팀)';
