-- Add playing_status column to lineups table
ALTER TABLE lineups
ADD COLUMN IF NOT EXISTS playing_status VARCHAR(10) DEFAULT 'playing';

-- Update existing records to have 'playing' status
UPDATE lineups
SET playing_status = 'playing'
WHERE playing_status IS NULL;
