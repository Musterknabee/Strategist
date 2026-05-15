"""Bridge strategy-batch evidence into Oracle sensor/advisory reports (paper-only; advisory)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.oracle_core import StrategyHealthSnapshot
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleSensorIngestionInput,
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
    OracleSensorRawSemanticInput,
)
from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult, StrategyRunStatus
from strategy_validator.validator.oracle_sensors import normalize_sensor_input
from strategy_validator.validator.oracle_opportunity_queue import build_oracle_opportunity_queue_report
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


_PREFERRED_RUN_IDS = (
    "oracle-next-batch",
    "full-runtime",
    "full-provider-paper",
    "full-gauntlet_batch",
    "prod-verify",
    "runtime-gauntlet-demo",
)


def discover_latest_batch_summary(artifact_root: Path | None = None) -> Path:
    """Return the best batch_summary.json for Oracle (preferred run_id, else newest mtime)."""
    root = (artifact_root or artifact_root_directory()).resolve()
    runs = root / "strategy_runs"
    if not runs.is_dir():
        raise FileNotFoundError(f"no strategy_runs under {root}")
    by_run: dict[str, Path] = {}
    for path in runs.glob("*/*/batch_summary.json"):
        run_id = path.parent.name
        by_run[run_id] = path
    for preferred in _PREFERRED_RUN_IDS:
        if preferred in by_run:
            return by_run[preferred]
    candidates = sorted(by_run.values(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"no batch_summary.json under {runs}")
    return candidates[0]


def strategy_health_snapshots_from_summary(summary: StrategyBatchRunSummary) -> list[StrategyHealthSnapshot]:
    out: list[StrategyHealthSnapshot] = []
    for r in summary.strategies:
        if r.status not in (StrategyRunStatus.PASSED, StrategyRunStatus.PAPER_ONLY):
            continue
        sharpe = float(r.sharpe_like if r.sharpe_like is not None else r.metrics.get("sharpe_like", 0.0))
        dsr = float(r.dsr_like_score if r.dsr_like_score is not None else 0.0)
        pbo = float(r.pbo_like_score if r.pbo_like_score is not None else 0.5)
        win = float(r.positive_fold_ratio if r.positive_fold_ratio is not None else 0.5)
        dd = abs(float(r.max_drawdown or 0.15))
        regimes: list[AdvisoryRegime] = ["TRANSITION"]
        if sharpe > 0.5 and dd < 0.12:
            regimes = ["RISK_ON_LOW_VOL"]
        elif dd > 0.2 or (r.warnings and any("REGIME_STRESS" in w for w in r.warnings)):
            regimes = ["RISK_OFF_HIGH_VOL"]
        prior = _clamp(0.35 + sharpe * 0.15 + win * 0.2 - dd * 0.5, 0.05, 0.95)
        out.append(
            StrategyHealthSnapshot(
                strategy_id=r.strategy_id,
                strategy_type=str(r.strategy_type or "unknown"),
                prior_edge_confidence=round(prior, 6),
                deflated_sharpe_ratio=round(dsr, 6),
                cpcv_lower_bound=round(dsr - pbo * 0.1, 6),
                realized_live_sharpe=round(sharpe, 6),
                recent_win_rate=round(_clamp(win, 0.0, 1.0), 6),
                drawdown_fraction=round(_clamp(dd, 0.0, 1.0), 6),
                expected_regimes=regimes,
            )
        )
    return out


def _semantic_from_batch(summary: StrategyBatchRunSummary) -> OracleSensorRawSemanticInput:
    blocked = sum(1 for s in summary.strategies if s.status == StrategyRunStatus.BLOCKED)
    failed = sum(1 for s in summary.strategies if s.status == StrategyRunStatus.FAILED)
    stress = sum(1 for s in summary.strategies if any("REGIME_STRESS" in w for w in (s.warnings or [])))
    n = max(len(summary.strategies), 1)
    pressure = _clamp((blocked + failed + stress) / n, 0.0, 1.0)
    hawk = 0.35 + pressure * 0.25
    dove = 0.35 - pressure * 0.15
    return OracleSensorRawSemanticInput(
        hawkish_document_ratio=round(hawk, 6),
        dovish_document_ratio=round(max(dove, 0.1), 6),
        geopolitical_headline_share=round(0.08 + pressure * 0.2, 6),
        contradiction_count=int(blocked + failed),
        belief_conflict_score=round(pressure * 0.6, 6),
    )


def _macro_from_batch(summary: StrategyBatchRunSummary) -> OracleSensorRawMacroInput:
    sharpes = [
        float(s.sharpe_like or s.metrics.get("sharpe_like", 0.0))
        for s in summary.strategies
        if s.sharpe_like is not None or s.metrics
    ]
    dds = [abs(float(s.max_drawdown or 0.1)) for s in summary.strategies]
    avg_sh = sum(sharpes) / len(sharpes) if sharpes else 0.0
    avg_dd = sum(dds) / len(dds) if dds else 0.15
    vol20 = _clamp(0.12 + avg_dd, 0.05, 0.45)
    vol252 = max(vol20, 0.08)
    return OracleSensorRawMacroInput(
        yield_curve_slope_bps=round(-30.0 + avg_sh * 20.0, 2),
        high_yield_credit_spread_bps=round(350.0 + avg_dd * 800.0, 2),
        equity_bond_correlation_20d=round(_clamp(-0.2 - avg_dd, -1.0, 1.0), 6),
        cross_asset_correlation_20d=round(_clamp(0.3 + avg_dd, -1.0, 1.0), 6),
        realized_volatility_20d=vol20,
        realized_volatility_252d=vol252,
    )


def _micro_from_batch(summary: StrategyBatchRunSummary) -> OracleSensorRawMicrostructureInput:
    passed = sum(1 for s in summary.strategies if s.status == StrategyRunStatus.PASSED)
    n = max(len(summary.strategies), 1)
    buy = 1.0 + passed
    sell = 1.0 + (n - passed)
    spread = 8.0 + (n - passed) * 2.0
    return OracleSensorRawMicrostructureInput(
        buy_volume=buy,
        sell_volume=sell,
        median_spread_bps=spread,
        baseline_spread_bps=8.0,
        top_book_depth_usd=5_000_000.0,
        baseline_top_book_depth_usd=6_000_000.0,
        toxic_flow_ratio=round(_clamp((n - passed) / n * 0.35, 0.0, 1.0), 6),
    )


def load_news_semantic_override(provider_samples_dir: Path) -> OracleSensorRawSemanticInput | None:
    """If a NewsAPI sample exists under provider_samples, derive semantic ratios from headline titles."""
    news_dir = provider_samples_dir / "newsapi"
    if not news_dir.is_dir():
        return None
    json_files = sorted(news_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not json_files:
        return None
    try:
        payload = json.loads(json_files[0].read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    articles = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(articles, list) or not articles:
        return None
    hawk_kw = ("rate", "inflation", "fed", "hike", "war", "sanction", "crisis")
    dove_kw = ("cut", "ease", "stimulus", "peace", "deal", "rally")
    geo_kw = ("war", "election", "china", "russia", "middle east", "tariff")
    hawk = dove = geo = 0
    for art in articles[:40]:
        if not isinstance(art, dict):
            continue
        title = str(art.get("title") or "").lower()
        if any(k in title for k in hawk_kw):
            hawk += 1
        if any(k in title for k in dove_kw):
            dove += 1
        if any(k in title for k in geo_kw):
            geo += 1
    total = max(hawk + dove, 1)
    return OracleSensorRawSemanticInput(
        hawkish_document_ratio=round(_clamp(hawk / total, 0.0, 1.0), 6),
        dovish_document_ratio=round(_clamp(dove / total, 0.0, 1.0), 6),
        geopolitical_headline_share=round(_clamp(geo / max(len(articles), 1), 0.0, 1.0), 6),
        contradiction_count=max(hawk, dove) // 3,
        belief_conflict_score=round(_clamp(abs(hawk - dove) / total, 0.0, 1.0), 6),
    )


def build_sensor_ingestion_from_batch(
    summary: StrategyBatchRunSummary,
    *,
    universe_label: str = "STRATEGIST_RESEARCH_UNIVERSE",
    provider_samples_dir: Path | None = None,
) -> OracleSensorIngestionInput:
    semantic = _semantic_from_batch(summary)
    if provider_samples_dir is not None:
        news = load_news_semantic_override(provider_samples_dir)
        if news is not None:
            semantic = news
    return OracleSensorIngestionInput(
        generated_for_utc=datetime.now(timezone.utc),
        universe_label=universe_label,
        macro_raw=_macro_from_batch(summary),
        semantic_raw=semantic,
        microstructure_raw=_micro_from_batch(summary),
        strategies=strategy_health_snapshots_from_summary(summary),
    )


def run_oracle_advisory_from_batch(
    summary: StrategyBatchRunSummary,
    *,
    artifact_root: Path,
    repo_root: Path,
    provider_samples_dir: Path | None = None,
) -> dict[str, Any]:
    """Normalize sensors, fuse signals, and emit strategic briefing artifacts."""
    art = artifact_root.resolve()
    samples_dir = provider_samples_dir
    if samples_dir is None:
        samples_dir = art / "provider_samples"
    if not (samples_dir / "newsapi").is_dir() and (repo_root / "artifacts" / "provider_samples" / "newsapi").is_dir():
        samples_dir = repo_root / "artifacts" / "provider_samples"
    out = art / "oracle_cycle" / "latest"
    out.mkdir(parents=True, exist_ok=True)

    ingestion = build_sensor_ingestion_from_batch(summary, provider_samples_dir=samples_dir)
    ingestion_path = out / "oracle_sensor_ingestion_input.json"
    ingestion_path.write_text(ingestion.model_dump_json(indent=2) + "\n", encoding="utf-8")

    ingest_report = normalize_sensor_input(ingestion)
    ingest_report_path = out / "oracle_sensor_ingestion_report.json"
    ingest_report_path.write_text(ingest_report.model_dump_json(indent=2) + "\n", encoding="utf-8")

    advisory = ingest_report.advisory_input
    advisory_path = out / "oracle_advisory_input.json"
    advisory_path.write_text(advisory.model_dump_json(indent=2) + "\n", encoding="utf-8")

    fusion = build_oracle_strategic_fusion_report(
        advisory,
        repo_root=repo_root,
        search_root=art,
    )
    fusion_path = out / "oracle_strategic_fusion_report.json"
    fusion_path.write_text(fusion.model_dump_json(indent=2) + "\n", encoding="utf-8")

    queue = build_oracle_opportunity_queue_report(advisory, fusion_report=fusion)
    queue_path = out / "oracle_opportunity_queue_report.json"
    queue_path.write_text(queue.model_dump_json(indent=2) + "\n", encoding="utf-8")

    news_source = "batch_derived"
    if load_news_semantic_override(samples_dir) is not None:
        news_source = "provider_samples/newsapi"

    return {
        "ok": True,
        "artifact_root": str(art),
        "output_dir": str(out),
        "batch_id": summary.batch_id,
        "run_id": summary.run_id,
        "strategy_snapshots": len(ingestion.strategies),
        "fusion_posture": fusion.strategic_posture,
        "dominant_regime": fusion.dominant_regime,
        "operator_readiness": fusion.operator_readiness,
        "fusion_summary": fusion.summary_line,
        "queue_summary": queue.summary_line,
        "top_operator_actions": list(fusion.operator_actions[:5]) + list(queue.operator_actions[:5]),
        "paths": {
            "ingestion_input": str(ingestion_path),
            "advisory_input": str(advisory_path),
            "fusion": str(fusion_path),
            "opportunity_queue": str(queue_path),
        },
        "news_semantic_source": news_source,
        "backtest_evidence": {
            "walk_forward_and_cpcv": "from_strategy_batch_gauntlet",
            "batch_summary_path": str(
                Path(summary.output_dir) / "batch_summary.json"
                if summary.output_dir
                else ""
            ),
        },
    }


def run_oracle_advisory_from_latest_batch(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = (repo_root or Path.cwd()).resolve()
    art = (artifact_root or artifact_root_directory(repo)).resolve()
    summary_path = discover_latest_batch_summary(art)
    summary = StrategyBatchRunSummary.model_validate(json.loads(summary_path.read_text(encoding="utf-8")))
    return run_oracle_advisory_from_batch(
        summary,
        artifact_root=art,
        repo_root=repo,
        provider_samples_dir=None,
    )
