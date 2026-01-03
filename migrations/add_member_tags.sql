-- Migration: Add tags feature for members
-- Date: 2026-01-03
-- Description: Adds tags table and member_tags junction table for tagging members

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    tag_id SERIAL PRIMARY KEY,
    room_id VARCHAR(8) REFERENCES rooms(room_id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_tag_per_room UNIQUE (room_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tag_room ON tags(room_id);

-- Create member_tags junction table
CREATE TABLE IF NOT EXISTS member_tags (
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(13) REFERENCES members(member_id) ON DELETE CASCADE NOT NULL,
    tag_id INTEGER REFERENCES tags(tag_id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_member_tag UNIQUE (member_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_member_tag_member ON member_tags(member_id);
CREATE INDEX IF NOT EXISTS idx_member_tag_tag ON member_tags(tag_id);

-- Add comments
COMMENT ON TABLE tags IS 'Member tags (e.g., club name, position, season)';
COMMENT ON TABLE member_tags IS 'Many-to-many relationship between members and tags';
COMMENT ON COLUMN tags.room_id IS 'Each room has its own set of tags';
COMMENT ON COLUMN tags.name IS 'Tag name (e.g., "동호회1", "가드", "25-1")';
