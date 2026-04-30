CREATE UNIQUE INDEX IF NOT EXISTS idx_operator_action_events_idempotency_key_unique
ON operator_action_events (json_extract(target_payload_json, '$.idempotency_key'))
WHERE json_extract(target_payload_json, '$.idempotency_key') IS NOT NULL
  AND json_extract(target_payload_json, '$.idempotency_key') != '';

INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description)
VALUES (4, datetime('now'), 'Durable operator action idempotency keys');
