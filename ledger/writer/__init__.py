import threading
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from strategy_validator.ledger.models.schema import ledger_table, engine, compute_row_hash, init_db
from strategy_validator.core.exceptions import ImmutableViolation, ConstitutionalViolation

# Internal token to guard write access
class _AdjudicationAuthority:
    def __init__(self, key: str):
        if key != "INTERNAL_SECRET_ONLY_FOR_ORCHESTRATOR":
            raise PermissionError("Unauthorized authority creation")

# Note: This is not exported to avoid easy import
_token = _AdjudicationAuthority("INTERNAL_SECRET_ONLY_FOR_ORCHESTRATOR")

def get_authority_token():
    """Gives the token to the authorized caller."""
    # In a real system, this would involve more complex checks.
    return _token

def append_event(authority: Any, experiment_id: str, event_type: str, state: str, payload: Dict[str, Any], manifest_hash: str, source: str):
    if not isinstance(authority, _AdjudicationAuthority):
        raise ConstitutionalViolation("Unauthorized write attempt to ledger.writer")

    init_db()
    with engine.begin() as conn:
        # Get last sequence and hash
        query = select(ledger_table.c.sequence_number, ledger_table.c.event_hash).where(
            ledger_table.c.experiment_id == experiment_id
        ).order_by(desc(ledger_table.c.sequence_number)).limit(1)
        
        row = conn.execute(query).fetchone()
        
        if row:
            next_seq = row.sequence_number + 1
            prev_hash = row.event_hash
        else:
            next_seq = 0
            prev_hash = "GENESIS"

        # Construct row data for hashing
        row_data = {
            "experiment_id": experiment_id,
            "sequence_number": next_seq,
            "event_type": event_type,
            "promotion_state": state,
            "event_payload_json": payload,
            "manifest_hash": manifest_hash,
            "adjudication_source": source
        }
        
        event_hash = compute_row_hash(row_data, prev_hash)
        
        # INSERT only
        stmt = ledger_table.insert().values(
            **row_data,
            event_hash=event_hash,
            previous_event_hash=prev_hash,
            created_at_utc=datetime.now(timezone.utc)
        )
        conn.execute(stmt)

# Explicitly prevent updates/deletes by not providing the functions.
# Any direct SQL execution would be caught by DBA/Security audits.
