from __future__ import annotations

from collections.abc import Callable, Mapping
import argparse

Runner = Callable[[argparse.Namespace], int]


def register_oracle_briefing_replay_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: Mapping[str, Runner],
) -> None:
    ocsi = sub.add_parser(
        "oracle-compacted-state-inspect",
        help="Inspect compacted checkpoint metadata against the canonical Oracle Event Log",
    )
    ocsi.add_argument("--log-path", required=True, help="Canonical ORACLE_EVENT_LOG.jsonl path")
    ocsi.add_argument("--checkpoint-metadata", required=True, help="ORACLE_DERIVED_VIEW checkpoint metadata JSON path")
    ocsi.add_argument("--output", default="", help="Write ORACLE_COMPACTED_STATE_INSPECTION_REPORT.json path")
    ocsi.add_argument("--markdown-output", default="", help="Write ORACLE_COMPACTED_STATE_INSPECTION_REPORT.md path")
    ocsi.set_defaults(_run=runners["oracle-compacted-state-inspect"])

    ocsr = sub.add_parser(
        "oracle-compacted-state-rebuild",
        help="Rebuild compacted checkpoint metadata from canonical Oracle Event Log truth",
    )
    ocsr.add_argument("--log-path", required=True, help="Canonical ORACLE_EVENT_LOG.jsonl path")
    ocsr.add_argument(
        "--checkpoint-metadata",
        required=True,
        help="Existing ORACLE_DERIVED_VIEW checkpoint metadata JSON path to rebuild in place",
    )
    ocsr.add_argument("--output", default="", help="Write ORACLE_COMPACTED_STATE_REBUILD_REPORT.json path")
    ocsr.add_argument("--markdown-output", default="", help="Write ORACLE_COMPACTED_STATE_REBUILD_REPORT.md path")
    ocsr.set_defaults(_run=runners["oracle-compacted-state-rebuild"])

    obp = sub.add_parser(
        "oracle-briefing-pack",
        help="Emit a canonical morning-review briefing pack with inline provenance and operator actions",
    )
    obp.add_argument("--repo-root", required=True, help="Repository root used to inspect canonical oracle/governance artifacts")
    obp.add_argument("--search-root", default="", help="Optional artifact search root, defaults to docs/artifacts under repo root")
    obp.add_argument("--derived-view-report", default="", help="Optional explicit ORACLE_DERIVED_VIEW / ORACLE_ROLLING_REVIEW JSON path")
    obp.add_argument("--constitutional-gate-report", default="", help="Optional explicit ORACLE_CONSTITUTIONAL_GATE_REPORT.json path")
    obp.add_argument("--closure-snapshot", default="", help="Optional explicit CLOSURE_SNAPSHOT.json path")
    obp.add_argument("--closure-dsse", default="", help="Optional explicit CLOSURE_SNAPSHOT.dsse.json path")
    obp.add_argument("--closure-public-key", default="", help="Optional explicit closure snapshot public key PEM path")
    obp.add_argument("--governed-exception", default="", help="Optional explicit GOVERNED_EXCEPTION_MEMO.json path")
    obp.add_argument("--governed-exception-dsse", default="", help="Optional explicit GOVERNED_EXCEPTION_MEMO.dsse.json path")
    obp.add_argument("--governed-exception-public-key", default="", help="Optional explicit governed exception public key PEM path")
    obp.add_argument("--strategic-briefing-report", default="", help="Optional explicit ORACLE_STRATEGIC_BRIEFING_REPORT.json path")
    obp.add_argument("--strategic-narrative-report", default="", help="Optional explicit ORACLE_STRATEGIC_NARRATIVE_REPORT.json path")
    obp.add_argument("--strategic-memory-horizon-report", default="", help="Optional explicit ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json path")
    obp.add_argument("--contradiction-resolution-report", default="", help="Optional explicit ORACLE_CONTRADICTION_RESOLUTION_REPORT.json path")
    obp.add_argument("--strategic-intervention-report", default="", help="Optional explicit ORACLE_STRATEGIC_INTERVENTION_REPORT.json path")
    obp.add_argument("--strategic-campaign-report", default="", help="Optional explicit ORACLE_STRATEGIC_CAMPAIGN_REPORT.json path")
    obp.add_argument("--strategic-campaign-execution-report", default="", help="Optional explicit ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json path")
    obp.add_argument("--thesis-memory-report", default="", help="Optional explicit ORACLE_THESIS_MEMORY_REPORT.json path")
    obp.add_argument("--research-priority-report", default="", help="Optional explicit ORACLE_RESEARCH_PRIORITY_REPORT.json path")
    obp.add_argument("--research-execution-memory-report", default="", help="Optional explicit ORACLE_RESEARCH_EXECUTION_MEMORY_REPORT.json path")
    obp.add_argument("--thesis-graph-report", default="", help="Optional explicit ORACLE_THESIS_GRAPH_REPORT.json path")
    obp.add_argument("--strategic-tension-report", default="", help="Optional explicit ORACLE_STRATEGIC_TENSION_REPORT.json path")
    obp.add_argument("--pack-root", default="", help="Optional directory where a materialized briefing pack bundle should be written")
    obp.add_argument("--output", default="", help="Write ORACLE_BRIEFING_PACK_REPORT.json path")
    obp.add_argument("--markdown-output", default="", help="Write ORACLE_BRIEFING_PACK_REPORT.md path")
    obp.add_argument("--html-output", default="", help="Write ORACLE_BRIEFING_PACK_REPORT.html path")
    obp.set_defaults(_run=runners["oracle-briefing-pack"])

    ora = sub.add_parser(
        "oracle-replay-audit",
        help="Compare canonical Event Log replay against compacted checkpoint state and optional checkpoint bundles",
    )
    ora.add_argument("--log-path", required=True, help="Canonical ORACLE_EVENT_LOG.jsonl path")
    ora.add_argument("--checkpoint-metadata", required=True, help="ORACLE_DERIVED_VIEW checkpoint metadata JSON path")
    ora.add_argument("--checkpoint-manifest", default="", help="Optional ORACLE_EVENT_CHECKPOINT.json path")
    ora.add_argument("--checkpoint-verification", default="", help="Optional ORACLE_EVENT_CHECKPOINT.verification.json path")
    ora.add_argument(
        "--rebuild-parity",
        action="store_true",
        help="Also compare the stored checkpoint metadata and derived report against a fresh deterministic rebuild from canonical Event Log truth",
    )
    ora.add_argument("--output", default="", help="Write ORACLE_REPLAY_AUDIT_REPORT.json path")
    ora.add_argument("--markdown-output", default="", help="Write ORACLE_REPLAY_AUDIT_REPORT.md path")
    ora.set_defaults(_run=runners["oracle-replay-audit"])

    ot = sub.add_parser(
        "oracle-transition",
        help="Compare two oracle evidence manifests and emit an advisory state-transition report",
    )
    ot.add_argument("previous_manifest", help="Previous ORACLE_EVIDENCE.json path")
    ot.add_argument("current_manifest", help="Current ORACLE_EVIDENCE.json path")
    ot.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    ot.add_argument("--previous-dsse", default="", help="Optional DSSE envelope for the previous oracle evidence manifest")
    ot.add_argument("--current-dsse", default="", help="Optional DSSE envelope for the current oracle evidence manifest")
    ot.add_argument("--previous-public-key", default="", help="Optional Ed25519 public key PEM for the previous manifest")
    ot.add_argument("--current-public-key", default="", help="Optional Ed25519 public key PEM for the current manifest")
    ot.add_argument("--output", default="", help="Write ORACLE_STATE_TRANSITION_REPORT.json path")
    ot.add_argument("--markdown-output", default="", help="Write ORACLE_STATE_TRANSITION_REPORT.md path")
    ot.set_defaults(_run=runners["oracle-transition"])
