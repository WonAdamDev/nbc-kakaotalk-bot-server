-- Migration: Add scheduled messages feature
-- Date: 2026-01-03
-- Description: Adds scheduled_messages table for automated message scheduling

-- Create scheduled_messages table
CREATE TABLE IF NOT EXISTS scheduled_messages (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(8) REFERENCES rooms(room_id) ON DELETE CASCADE NOT NULL,
    message TEXT NOT NULL,
    scheduled_time TIME NOT NULL,
    days_of_week INTEGER[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_message_room ON scheduled_messages(room_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_message_active ON scheduled_messages(is_active);

-- Add comments
COMMENT ON TABLE scheduled_messages IS 'Scheduled messages sent by bot at specific times';
COMMENT ON COLUMN scheduled_messages.message IS 'Message content to send';
COMMENT ON COLUMN scheduled_messages.scheduled_time IS 'Time of day to send (e.g., 09:00, 18:00)';
COMMENT ON COLUMN scheduled_messages.days_of_week IS 'Days to send (1=Monday, 2=Tuesday, ..., 7=Sunday)';
COMMENT ON COLUMN scheduled_messages.is_active IS 'Whether this scheduled message is active';
COMMENT ON COLUMN scheduled_messages.created_by IS 'Admin who created this scheduled message';
