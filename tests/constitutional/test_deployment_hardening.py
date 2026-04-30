import pytest
import sqlite3
from datetime import datetime, timezone
from strategy_validator.core.enums import RuntimeMode, PromotionState, EvidenceType
from strategy_validator.core.exceptions import AdjudicationError
from strategy_validator.validator.readiness import perform_readiness_check, generate_operational_diagnostics
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import EvidenceBundle, Evidence, ReproducibilityManifest
from strategy_validator.migrations import apply_sqlite_migrations

@pytest.fixture
def prod_env(monkeypatch, tmp_path):
    db_path = tmp_path / "production_ledger.sqlite3"
    conn = sqlite3.connect(db_path)
    try:
        apply_sqlite_migrations(conn)
    finally:
        conn.close()
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.resolve()))
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "abcdefghijklmnopqrstuvwxyz1234567890")
    monkeypatch.setenv(
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
        "operator:command:write,operator:projection:read",
    )

def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64, data_snapshot_hash="b" * 64, universe_hash="c" * 64,
        feature_graph_hash="d" * 64, parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1", cost_model_version="v1", calendar_version="v1"
    )

def _exp(eid: str) -> ExperimentManifest:
    bundle = EvidenceBundle(
        reproducibility=_repro(),
        benchmark_rung="L1",
        search_breadth=3,
        evaluation_time_utc=datetime(2026, 4, 12, tzinfo=timezone.utc),
        market_data_subject_id="portfolio"
    )
    return ExperimentManifest(
        experiment_id=eid,
        strategy_name="test_strat",
        version="1.0",
        proposer_id="user_1",
        evidence_bundle=bundle,
        state=PromotionState.PROMOTABLE
    )

@pytest.mark.constitutional
class TestDeploymentHardening:
    def test_startup_readiness_blocks_relative_path_in_production(self, monkeypatch):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "relative/ledger.sqlite3")
        
        report = perform_readiness_check()
        assert report.status == "BLOCKED"
        # Can be either code depending on whether resolve_database_path raises or returns
        assert any(b.code in ("UNSAFE_LEDGER_PATH", "LEDGER_ACCESS_FAILED") for b in report.blockers)

    def test_startup_readiness_blocks_incompatible_schema(self, monkeypatch, tmp_path):
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "abcdefghijklmnopqrstuvwxyz1234567890")
        monkeypatch.setenv(
            "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
            "operator:command:write,operator:projection:read",
        )
        # Create a DB with old schema version
        db_path = tmp_path / "old_ledger.sqlite3"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE _schema_version_tracking (version_id INTEGER PRIMARY KEY, applied_at_utc TEXT)")
        conn.execute("INSERT INTO _schema_version_tracking (version_id, applied_at_utc) VALUES (1, '2026-01-01')")
        conn.commit()
        conn.close()

        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(db_path.absolute()))
        # Mock migrations to prevent auto-upgrade
        monkeypatch.setattr("strategy_validator.ledger._append_only.apply_sqlite_migrations", lambda x: None)
        
        report = perform_readiness_check()
        assert report.status == "BLOCKED"
        assert any(b.code == "LEDGER_SCHEMA_NOT_CURRENT" for b in report.blockers)
        assert report.schema_version == 1

    def test_adjudicate_enforces_readiness_blocking(self, monkeypatch, prod_env):
        # Sabotage path to trigger block
        monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "unsafe/relative/path")
        
        exp = _exp("BLOCKED-RUN")
        with pytest.raises(AdjudicationError, match="Production adjudication blocked by readiness"):
            adjudicate(exp, commit=False)

    def test_diagnostics_capture_mode_and_fingerprint(self, prod_env):
        diag = generate_operational_diagnostics()
        assert diag.runtime_mode == RuntimeMode.PRODUCTION
        assert diag.config_fingerprint is not None
        assert len(diag.config_fingerprint) == 64
        assert diag.readiness_status == "READY"
        assert diag.production_safe_adjudication_allowed is True

    def test_fingerprint_changes_on_config_mutation(self, monkeypatch):
        # Baseline
        f1 = perform_readiness_check().config_fingerprint
        
        # Mutate config via environment (if config supports it) or mock load_config
        # For simplicity, we'll check that identical config yields identical fingerprint
        f2 = perform_readiness_check().config_fingerprint
        assert f1 == f2
        
        # Mutate mode
        monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "PRODUCTION")
        f3 = perform_readiness_check().config_fingerprint
        assert f3 != f1

    def test_decision_provenance_contains_readiness_linkage(self, prod_env):
        exp = _exp("PROVENANCE-CHECK")
        adjudicate(exp)
        decision = exp.promotion_history[-1]
        
        assert decision.runtime_mode == RuntimeMode.PRODUCTION
        assert decision.config_fingerprint is not None
        assert len(decision.config_fingerprint) == 64
