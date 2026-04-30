CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_action_events_sequence_unique
ON operator_action_events (sequence_number)
WHERE sequence_number IS NOT NULL;

INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description)
VALUES (5, datetime('now'), 'Durable operator action sequence uniqueness');
