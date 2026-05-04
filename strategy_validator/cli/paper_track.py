"""CLI: paper tracking enroll / snapshot / evaluate (evidence only; no broker)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from datetime import date

from strategy_validator.application.paper_tracking_ops import (
    _paper_tracking_root,
    append_daily_snapshot,
    assess_paper_tracking,
    enroll_strategies_from_batch_run,
    evaluate_paper_tracking,
    list_paper_tracking_entries,
    run_paper_tracking_daily,
)
from strategy_validator.application.promotion_review_ops import build_promotion_review_packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_en = sub.add_parser("enroll", help="Enroll gauntlet-passed strategies from a batch run directory")
    p_en.add_argument(
        "--batch-run",
        required=True,
        help="Path to batch run directory containing batch_summary.json",
    )
    p_en.add_argument(
        "--strategy-id",
        action="append",
        default=[],
        help="Limit to strategy id (repeatable); default all eligible",
    )
    p_en.add_argument(
        "--allow-synthetic-demo",
        action="store_true",
        help="Allow PAPER_ONLY synthetic rows as DEMO_PAPER_ONLY tracking",
    )
    p_en.add_argument("--json", action="store_true", help="Emit JSON on stdout")

    p_sn = sub.add_parser("snapshot", help="Append deterministic daily signal + outcome snapshots")
    p_sn.add_argument("--tracking-id", required=True, help="Paper tracking id (directory name)")
    p_sn.add_argument(
        "--as-of",
        default="",
        help="Observation date YYYY-MM-DD (default: today or test clock)",
    )
    p_sn.add_argument("--json", action="store_true")

    p_ev = sub.add_parser("evaluate", help="Evaluate kill rules and write scorecard")
    p_ev.add_argument("--tracking-id", required=True)
    p_ev.add_argument("--json", action="store_true")

    p_as = sub.add_parser("assess", help="Governance lifecycle assessment (writes lifecycle_assessment.json)")
    p_as.add_argument("--tracking-id", required=True)
    p_as.add_argument("--json", action="store_true")
    p_as.add_argument(
        "--allow-promotion-despite-duplicative",
        action="store_true",
        help="Set manifest governance allow_promotion_despite_duplicative (requires --duplicative-rationale)",
    )
    p_as.add_argument(
        "--duplicative-rationale",
        default="",
        help="Non-empty rationale when overriding DUPLICATIVE promotion block",
    )
    p_as.add_argument(
        "--mark-rejected",
        action="store_true",
        help="Set manifest governance lifecycle_rejected",
    )

    p_ls = sub.add_parser("list", help="List enrolled paper tracking directories")
    p_ls.add_argument("--json", action="store_true")

    p_pr = sub.add_parser("promotion-packet", help="Build promotion_review_packet.json (human review evidence only)")
    p_pr.add_argument("--tracking-id", required=True)
    p_pr.add_argument("--json", action="store_true")

    p_rd = sub.add_parser("run-daily", help="Snapshot, evaluate, assess all tracking dirs; write daily_run_manifest")
    p_rd.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_rd.add_argument(
        "--tracking-root",
        default="",
        help="Override paper tracking root (else env STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT or default)",
    )
    p_rd.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)

    if ns.cmd == "enroll":
        run_dir = Path(ns.batch_run)
        try:
            manifests = enroll_strategies_from_batch_run(
                run_dir,
                strategy_ids=ns.strategy_id or None,
                allow_synthetic_demo=ns.allow_synthetic_demo,
            )
        except FileNotFoundError as e:
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{e}\n")
            return 2
        root = _paper_tracking_root()
        payload = {
            "ok": True,
            "enrolled_count": len(manifests),
            "tracking_ids": [m.tracking_id for m in manifests],
            "manifest_paths": [str(root / m.tracking_id / "paper_tracking_manifest.json") for m in manifests],
        }
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"enrolled {len(manifests)} tracking id(s): {payload['tracking_ids']}\n")
        return 0

    if ns.cmd == "snapshot":
        obs = None
        if ns.as_of.strip():
            obs = date.fromisoformat(ns.as_of.strip())
        try:
            sig, out = append_daily_snapshot(ns.tracking_id, observation_date=obs)
        except FileNotFoundError as e:
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{e}\n")
            return 2
        payload = {
            "ok": True,
            "tracking_id": ns.tracking_id,
            "signal_date": sig.observation_date_utc.isoformat(),
            "signal_digest": sig.evidence_sha256,
            "outcome_digest": out.evidence_sha256,
        }
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"snapshot {sig.observation_date_utc} signal={sig.evidence_sha256[:12]}...\n")
        return 0

    if ns.cmd == "evaluate":
        try:
            sc = evaluate_paper_tracking(ns.tracking_id)
        except FileNotFoundError as e:
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{e}\n")
            return 2
        payload = {
            "ok": True,
            "tracking_id": ns.tracking_id,
            "kill_state": sc.kill_state.value,
            "cumulative_paper_return": sc.cumulative_paper_return,
            "drift_score": sc.drift_score,
            "triggered_rules": [t.model_dump(mode="json") for t in sc.triggered_rules],
            "scorecard_sha256": sc.scorecard_sha256,
        }
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"evaluate kill_state={sc.kill_state.value} return={sc.cumulative_paper_return:.4f}\n")
        return 0

    if ns.cmd == "assess":
        rationale = ns.duplicative_rationale.strip()
        if ns.allow_promotion_despite_duplicative and not rationale:
            err = "DUPLICATIVE_OVERRIDE_REQUIRES_RATIONALE"
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": err}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{err}\n")
            return 2
        allow_dup = True if ns.allow_promotion_despite_duplicative else None
        rat_arg = rationale if ns.allow_promotion_despite_duplicative else None
        rej = True if ns.mark_rejected else None
        try:
            assessment = assess_paper_tracking(
                ns.tracking_id,
                allow_promotion_despite_duplicative=allow_dup,
                duplicative_promotion_rationale=rat_arg,
                lifecycle_rejected=rej,
            )
        except FileNotFoundError as e:
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{e}\n")
            return 2
        payload = {
            "ok": True,
            "tracking_id": ns.tracking_id,
            "lifecycle_state": assessment.current_state.value,
            "kill_rule_status": assessment.kill_rule_status,
            "blockers": assessment.blockers,
            "basis_summary": assessment.basis_summary,
            "manifest_sha256": assessment.manifest_sha256,
            "paper_tracking_scorecard_digest": assessment.paper_tracking_scorecard_digest,
            "lifecycle_assessment_sha256": assessment.lifecycle_assessment_sha256,
            "promotion_review_disclaimer": assessment.promotion_review_disclaimer,
            "promotion_review_ready": assessment.promotion_review_ready,
        }
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"assess lifecycle_state={assessment.state.value}\n")
        return 0

    if ns.cmd == "list":
        entries = list_paper_tracking_entries()
        payload = {"ok": True, "schema_version": "paper_tracking_list/v1", "entries": entries}
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"{len(entries)} paper tracking entr(y/ies)\n")
            for row in entries:
                sys.stdout.write(f"  {row['tracking_id']}  {row['strategy_id']}  {row['lifecycle_state']}\n")
        return 0

    if ns.cmd == "promotion-packet":
        try:
            pkt = build_promotion_review_packet(ns.tracking_id)
        except FileNotFoundError as e:
            if ns.json:
                sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True) + "\n")
            else:
                sys.stderr.write(f"{e}\n")
            return 2
        payload = {
            "ok": True,
            "packet_id": pkt.packet_id,
            "tracking_id": pkt.tracking_id,
            "recommendation": pkt.recommendation.recommendation.value,
            "rationale": pkt.recommendation.rationale,
            "packet_sha256": pkt.packet_sha256,
            "path": str(_paper_tracking_root() / ns.tracking_id / "promotion_review_packet.json"),
        }
        if ns.json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(f"promotion-packet {payload['recommendation']} packet_id={payload['packet_id']}\n")
        return 0

    if ns.cmd == "run-daily":
        d = date.fromisoformat(ns.date.strip())
        tr = Path(ns.tracking_root).resolve() if ns.tracking_root.strip() else None
        payload = run_paper_tracking_daily(d, tracking_root=tr)
        out = {"ok": True, **payload}
        if ns.json:
            sys.stdout.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(
                f"daily_run date={payload['run_date_utc']} ok={payload['failure_count'] == 0} "
                f"processed={len(payload['processed_tracking_ids'])}\n"
            )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
