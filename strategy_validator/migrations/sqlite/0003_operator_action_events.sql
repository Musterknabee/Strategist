CREATE TABLE IF NOT EXISTS operator_action_events (
    action_event_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    target_payload_json TEXT NOT NULL,
    accepted INTEGER NOT NULL,
    status TEXT NOT NULL,
    summary_line TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE,
    sequence_number INTEGER,
    previous_event_hash TEXT
);

CREATE INDEX IF NOT EXISTS idx_operator_action_events_operator_created
ON operator_action_events (operator_id, created_at_utc);

CREATE INDEX IF NOT EXISTS idx_operator_action_events_sequence
ON operator_action_events (sequence_number, created_at_utc, action_event_id);

CREATE INDEX IF NOT EXISTS idx_operator_action_events_idempotency_key
ON operator_action_events (json_extract(target_payload_json, '$.idempotency_key'));

INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description)
VALUES (3, datetime('now'), 'Operator action journal');
