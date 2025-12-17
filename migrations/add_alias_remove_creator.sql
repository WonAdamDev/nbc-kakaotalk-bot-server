-- Migration: Add alias field and remove creator field from games table
-- Date: 2024-12-16
-- Description: Adds alias field for game nickname and removes creator field (always Admin)

-- Add alias column (defaults to date if not provided)
ALTER TABLE games ADD COLUMN IF NOT EXISTS alias VARCHAR(100);

-- Update existing games to use date as alias where alias is null
-- Use TO_CHAR for proper date formatting and COALESCE for NULL dates
UPDATE games SET alias = COALESCE(TO_CHAR(date, 'YYYY-MM-DD'), 'Unknown') WHERE alias IS NULL OR alias = '';

-- Make alias NOT NULL after setting default values
ALTER TABLE games ALTER COLUMN alias SET NOT NULL;

-- Remove creator column (always Admin now)
ALTER TABLE games DROP COLUMN IF EXISTS creator;

-- Add comment for documentation
COMMENT ON COLUMN games.alias IS 'Game nickname/alias for easy searching (defaults to date if not provided)';
