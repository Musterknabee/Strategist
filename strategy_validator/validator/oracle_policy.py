from __future__ import annotations

import hashlib
import json
from pathlib import Path

from strategy_validator.contracts.oracle_core import OraclePolicyArtifact
from strategy_validator.validator.oracle_schema_registry import load_registered_artifact


def _default_policy_path(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root.resolve() / "strategy_validator" / "policies" / "oracle_policy.json"
    return Path(__file__).resolve().parents[1] / "policies" / "oracle_policy.json"


def load_oracle_policy(*, repo_root: Path | None = None, policy_path: Path | None = None) -> tuple[OraclePolicyArtifact, Path]:
    candidate = (policy_path or _default_policy_path(repo_root)).resolve()
    if not candidate.exists() and policy_path is None:
        candidate = _default_policy_path(None).resolve()
    _, _, model = load_registered_artifact(
        candidate,
        expected_schemas={"oracle_policy_artifact/v1"},
        expected_families={"oracle"},
    )
    return model, candidate


def oracle_policy_sha256(*, repo_root: Path | None = None, policy_path: Path | None = None) -> tuple[str, str, str]:
    policy, resolved = load_oracle_policy(repo_root=repo_root, policy_path=policy_path)
    stable = json.dumps(policy.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    digest = hashlib.sha256(stable).hexdigest()
    return policy.policy_version, digest, str(resolved)
