-- Schema version tracking for forensic ledger
CREATE TABLE IF NOT EXISTS _schema_version_tracking (
    version_id INTEGER PRIMARY KEY,
    applied_at_utc TEXT NOT NULL,
    description TEXT
);

-- Initialize version 1 if not exists
INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description)
VALUES (1, datetime('now'), 'Initial ledger schema');

-- Mark version 2 (Operational Hardening)
INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description)
VALUES (2, datetime('now'), 'Operational readiness hardening');
