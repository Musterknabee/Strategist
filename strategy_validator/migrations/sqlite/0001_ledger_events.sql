CREATE TABLE IF NOT EXISTS ledger_events (
    experiment_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    promotion_state TEXT NOT NULL,
    event_payload_json TEXT NOT NULL,
    manifest_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE,
    previous_event_hash TEXT,
    created_at_utc TEXT NOT NULL,
    writer_identity TEXT NOT NULL,
    PRIMARY KEY (experiment_id, sequence_number)
);
