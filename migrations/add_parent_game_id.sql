-- Migration: Add parent_game_id field to games table
-- Date: 2024-12-16
-- Description: Adds parent game reference for tracking original game when using continue feature

-- Add parent_game_id column with self-referential foreign key
ALTER TABLE games ADD COLUMN IF NOT EXISTS parent_game_id VARCHAR(8);

-- Add foreign key constraint (references same table)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'games_parent_game_id_fkey'
    ) THEN
        ALTER TABLE games
        ADD CONSTRAINT games_parent_game_id_fkey
        FOREIGN KEY (parent_game_id)
        REFERENCES games(game_id)
        ON DELETE SET NULL;
    END IF;
END $$;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_games_parent_game_id ON games(parent_game_id);

-- Add comment for documentation
COMMENT ON COLUMN games.parent_game_id IS 'Original game ID when using continue feature (self-referential)';
