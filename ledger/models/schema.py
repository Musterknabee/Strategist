from datetime import datetime, timezone
import hashlib
import json
from sqlalchemy import MetaData, Table, Column, String, Integer, DateTime, JSON, ForeignKey, create_engine, select, insert

metadata = MetaData()

# The Ledger Table: Append-only by design in our application logic
ledger_table = Table(
    "ledger_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("experiment_id", String(50), nullable=False, index=True),
    Column("sequence_number", Integer, nullable=False),
    Column("event_type", String(50), nullable=False),
    Column("promotion_state", String(50), nullable=False),
    Column("event_payload_json", JSON, nullable=False),
    Column("manifest_hash", String(64), nullable=False),
    Column("event_hash", String(64), nullable=False, unique=True),
    Column("previous_event_hash", String(64), nullable=False),
    Column("created_at_utc", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)),
    Column("adjudication_source", String(100), nullable=False),
)

def compute_row_hash(data: dict, prev_hash: str) -> str:
    """Computes a SHA256 hash of the row content + previous hash."""
    payload = json.dumps(data, sort_keys=True, default=str)
    content = f"{payload}|{prev_hash}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

DB_URL = "sqlite:///strategy_ledger.db"
engine = create_engine(DB_URL)

def init_db():
    metadata.create_all(engine)
