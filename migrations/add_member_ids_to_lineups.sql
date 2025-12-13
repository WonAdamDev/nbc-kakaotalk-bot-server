-- Add member_id columns to lineups table for player tracking

-- Add member_id column (MEM_X7Y2K9P3 or GST_X7Y2K9P3)
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS member_id VARCHAR(13);

-- Add is_guest column
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE;

-- Add team_id_snapshot column (team ID at the time of game)
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS team_id_snapshot VARCHAR(13);

-- Add indexes for query optimization
CREATE INDEX IF NOT EXISTS idx_lineup_member_id ON lineups(member_id);
CREATE INDEX IF NOT EXISTS idx_lineup_is_guest ON lineups(is_guest);

-- Existing data will have NULL member_id (legacy data)
-- is_guest defaults to FALSE (existing data treated as members)

-- Column descriptions:
-- member_id: Player ID (MEM_xxx: room member, GST_xxx: guest player)
-- is_guest: Guest flag (excluded from statistics)
-- team_id_snapshot: Team ID snapshot at the time of game
