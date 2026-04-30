import hashlib
import json
from typing import Any, Dict

def compute_manifest_hash(data: Dict[str, Any]) -> str:
    """Computes a deterministic SHA256 hash for an experiment manifest."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def verify_integrity(data: Dict[str, Any], expected_hash: str) -> bool:
    return compute_manifest_hash(data) == expected_hash
