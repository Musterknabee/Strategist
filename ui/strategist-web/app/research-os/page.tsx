"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsStatus } from "@/hooks/useUiResearchOsStatus";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchOsPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsStatus();
  const root = q.data != null ? asRecord(q.data) : null;

  const tape: TapeLine[] = useMemo(() => {
    const ts = asString(root?.generated_at_utc);
    const deg = root?.degraded != null ? asStringArray(root.degraded) : [];
    return [
      {
        id: "ros",
        ts,
        severity: deg.length ? "warn" : "ok",
        text: `RESEARCH_OS ${deg.length ? `DEGRADED:${deg.length}` : "OK"}`,
      },
    ];
  }, [root]);

  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  const artSummary = root?.artifact_root_summary != null ? asRecord(root.artifact_root_summary as object) : null;
  const runtimeDemo = root?.runtime_demo_manifest != null ? asRecord(root.runtime_demo_manifest as object) : null;
  const gauntlet = root?.gauntlet_latest != null ? asRecord(root.gauntlet_latest as object) : null;
  const paper = root?.paper_tracking_latest != null ? asRecord(root.paper_tracking_latest as object) : null;
  const promo = root?.promotion_packet_latest != null ? asRecord(root.promotion_packet_latest as object) : null;
  const broker = root?.paper_broker_status != null ? asRecord(root.paper_broker_status as object) : null;
  const compute = root?.compute_status != null ? asRecord(root.compute_status as object) : null;
  const demo = root?.demo_manifest != null ? asRecord(root.demo_manifest as object) : null;
  const provider = root?.provider_ingestion_latest != null ? asRecord(root.provider_ingestion_latest as object) : null;
  const providerLoop =
    root?.provider_paper_loop_latest != null ? asRecord(root.provider_paper_loop_latest as object) : null;
  const providerHist =
    root?.provider_historical_snapshot_latest != null ? asRecord(root.provider_historical_snapshot_latest as object) : null;
  const brokerArt =
    root?.paper_broker_status_latest != null ? asRecord(root.paper_broker_status_latest as object) : null;
  const provGaunt =
    root?.provider_backed_gauntlet_latest != null ? asRecord(root.provider_backed_gauntlet_latest as object) : null;
  const daily = root?.daily_tracking_latest != null ? asRecord(root.daily_tracking_latest as object) : null;
  const cpcv = root?.cpcv_latest != null ? asRecord(root.cpcv_latest as object) : null;
  const portfolio = root?.portfolio_allocation_latest != null ? asRecord(root.portfolio_allocation_latest as object) : null;
  const latestPaper = paper?.latest != null ? asRecord(paper.latest as object) : null;
  const trackingId = asString(latestPaper?.tracking_id as string);

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research OS</h1>
          <p className="muted">
            Consolidated read-plane status · evidence only · no live trading · no broker orders from browser · promotion
            packets are not live approval
          </p>
        </div>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Status rail" dense onInspect={() => openInspector({ title: "Research OS status", rawJson: root ?? {} })}>
          {q.isLoading && <p className="muted">Loading…</p>}
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/status</p>}
          {root && (
            <div style={{ fontSize: "11px", display: "grid", gap: "0.5rem" }}>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                <span className="muted">Degraded</span>
                <span>{(asStringArray(root.degraded).length ? asStringArray(root.degraded).join(", ") : "—") as string}</span>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                <span className="muted">Warnings</span>
                <span>{(asStringArray(root.warnings).length ? asStringArray(root.warnings).join("; ") : "—") as string}</span>
              </div>
            </div>
          )}
        </Pane>

        <Pane
          title="Artifact roots (API scan)"
          dense
          onInspect={() => openInspector({ title: "Artifact roots", rawJson: artSummary ?? {} })}
        >
          {!artSummary ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "artifact_root", v: asString(artSummary.artifact_root as string) ?? "—" },
                { k: "strategy_batch_scan", v: asString(artSummary.strategy_batch_scan_root as string) ?? "—" },
                { k: "paper_tracking_scan", v: asString(artSummary.paper_tracking_scan_root as string) ?? "—" },
                { k: "strategy_data", v: asString(artSummary.strategy_data_root as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Runtime demo manifest"
          dense
          onInspect={() => openInspector({ title: "Runtime demo manifest", rawJson: runtimeDemo ?? {} })}
        >
          {!runtimeDemo || runtimeDemo.status === "NOT_PRESENT" ? (
            <p className="muted">
              No runtime_demo_manifest.json — run{" "}
              <code className="json-preview">strategy-validator-research-os-runtime-demo</code> or host script (see
              docs).
            </p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(runtimeDemo.status as string) ?? "—"} /> },
                { k: "ok", v: String(runtimeDemo.ok ?? "—") },
                { k: "run_id", v: asString(runtimeDemo.run_id as string) ?? "—" },
                { k: "generated_at", v: asString(runtimeDemo.generated_at_utc as string) ?? "—" },
                { k: "artifact_root", v: asString(runtimeDemo.artifact_root as string) ?? "—" },
                { k: "digest", v: asString(runtimeDemo.manifest_sha256 as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Provider-backed paper loop"
          dense
          onInspect={() => openInspector({ title: "Provider paper loop", rawJson: providerLoop ?? {} })}
        >
          {!providerLoop || providerLoop.status === "NOT_PRESENT" ? (
            <p className="muted">
              No provider_paper_loop_manifest.json — run{" "}
              <code className="json-preview">strategy-validator-provider-paper-loop</code> or{" "}
              <code className="json-preview">python scripts/run_provider_paper_loop.py</code> (fixture-first; see docs).
            </p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(providerLoop.status as string) ?? "—"} /> },
                { k: "ok", v: String(providerLoop.ok ?? "—") },
                { k: "run_id", v: asString(providerLoop.run_id as string) ?? "—" },
                { k: "generated_at", v: asString(providerLoop.generated_at_utc as string) ?? "—" },
                {
                  k: "historical_snapshot_run",
                  v: <StatusBadge raw={asString(providerHist?.status as string) ?? "—"} />,
                },
                {
                  k: "broker_status_artifact",
                  v: <StatusBadge raw={asString(brokerArt?.status as string) ?? "—"} />,
                },
                {
                  k: "provider_strategies_in_latest_batch",
                  v: String(provGaunt?.provider_snapshot_strategy_count ?? "—"),
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Gauntlet (latest batch)"
          dense
          onInspect={() => openInspector({ title: "Gauntlet latest", rawJson: gauntlet ?? {} })}
        >
          {!gauntlet ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "batch_id", v: asString(gauntlet.batch_id) ?? "—" },
                { k: "run_id", v: asString(gauntlet.run_id) ?? "—" },
                { k: "ok", v: String(gauntlet.ok ?? "—") },
                { k: "strategies", v: String(gauntlet.strategy_count ?? "—") },
                { k: "passed", v: String(gauntlet.passed_count ?? "—") },
                { k: "paper_only", v: String(gauntlet.paper_only_count ?? "—") },
                { k: "blocked", v: String(gauntlet.blocked_count ?? "—") },
                { k: "failed", v: String(gauntlet.failed_count ?? "—") },
                {
                  k: "top_candidate",
                  v: asString((gauntlet.top_candidate as { strategy_id?: string } | undefined)?.strategy_id) ?? "—",
                },
                {
                  k: "provider_snapshot_strategies",
                  v: String(provGaunt?.provider_snapshot_strategy_count ?? "—"),
                },
                { k: "summary_path", v: asString(gauntlet.summary_path) ?? "—" },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.5rem", fontSize: "10px" }}>
            docker exec strategist-local-api strategy-validator-research-os-runtime-demo --artifact-root
            /var/lib/strategy-validator/artifacts --run-id my-run --allow-synthetic-demo --overwrite --skip-benchmark
            --json
          </pre>
        </Pane>

        <Pane
          title="Paper tracking & lifecycle"
          dense
          onInspect={() => openInspector({ title: "Paper latest", rawJson: paper ?? {} })}
        >
          {!paper?.latest ? (
            <p className="muted">No paper tracking bundle detected under scan root.</p>
          ) : (
            <TermKV
              rows={[
                { k: "tracking_id", v: trackingId || "—" },
                {
                  k: "kill_posture",
                  v: asString(latestPaper?.lifecycle_kill_rule_posture as string) ?? "—",
                },
                {
                  k: "lifecycle",
                  v: asString(latestPaper?.lifecycle_state as string) ?? "—",
                },
                {
                  k: "promotion_review_ready",
                  v: String((latestPaper?.promotion_review_ready as boolean | undefined) ?? false),
                },
                {
                  k: "promotion_packet",
                  v: <StatusBadge raw={asString(promo?.recommendation as string) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Lifecycle / promotion (evidence only)"
          dense
          onInspect={() => openInspector({ title: "Lifecycle / promotion", rawJson: { lifecycle: root?.lifecycle_latest, promo } })}
        >
          <p className="muted" style={{ fontSize: "11px", marginBottom: "0.5rem" }}>
            READY_FOR_HUMAN_REVIEW is an evidence gate for operators, not automated live promotion.
          </p>
          {!latestPaper ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "state", v: asString(latestPaper.lifecycle_state as string) ?? "—" },
                {
                  k: "recommendation",
                  v: <StatusBadge raw={asString(promo?.recommendation as string) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Provider ingestion (artifacts)"
          dense
          onInspect={() => openInspector({ title: "Provider ingestion", rawJson: provider ?? {} })}
        >
          {!provider ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: <StatusBadge raw={asString(provider.status) ?? "—"} /> },
                { k: "provider_status", v: asString(provider.provider_status as string) ?? "—" },
                { k: "pit_status", v: asString(provider.pit_status as string) ?? "—" },
                { k: "artifact_path", v: asString(provider.artifact_path as string) ?? "—" },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Daily paper tracking"
          dense
          onInspect={() => openInspector({ title: "Daily tracking", rawJson: daily ?? {} })}
        >
          {!daily || Object.keys(daily).length === 0 ? (
            <p className="muted">No daily_run manifest found under paper scan root.</p>
          ) : (
            <TermKV
              rows={[
                { k: "manifest_path", v: asString(daily.manifest_path as string) ?? "—" },
                { k: "run_date_utc", v: asString(daily.run_date_utc as string) ?? "—" },
                { k: "failure_count", v: String((daily.failure_count as number | undefined) ?? "—") },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="CPCV / robustness (from latest batch)"
          dense
          onInspect={() => openInspector({ title: "CPCV hint", rawJson: cpcv ?? {} })}
        >
          {!cpcv ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "hint_status", v: asString(cpcv.status as string) ?? "—" },
                {
                  k: "strategies_with_cpcv_fields",
                  v: String(Array.isArray(cpcv.strategies) ? cpcv.strategies.length : 0),
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Portfolio allocation (latest batch dir)"
          dense
          onInspect={() => openInspector({ title: "Portfolio allocation", rawJson: portfolio ?? {} })}
        >
          {!portfolio || Object.keys(portfolio).length === 0 ? (
            <p className="muted">No portfolio_allocation_result.json next to latest batch summary.</p>
          ) : (
            <TermKV
              rows={[
                {
                  k: "gate",
                  v: <StatusBadge raw={asString(portfolio.allocation_gate_status as string) ?? "—"} />,
                },
                {
                  k: "excluded_n",
                  v: String(Array.isArray(portfolio.excluded) ? portfolio.excluded.length : 0),
                },
                {
                  k: "warnings_n",
                  v: String(Array.isArray(portfolio.warnings) ? portfolio.warnings.length : 0),
                },
                {
                  k: "blockers_n",
                  v: String(Array.isArray(portfolio.blockers) ? portfolio.blockers.length : 0),
                },
              ]}
            />
          )}
          {portfolio?.allocation_gate_status === "BLOCKED" && (
            <p className="muted" style={{ fontSize: "11px", marginTop: "0.35rem" }}>
              BLOCKED is a documented gate outcome (e.g. correlation / eligibility), not a UI error.
            </p>
          )}
        </Pane>

        <Pane
          title="Paper broker policy (env)"
          dense
          onInspect={() => openInspector({ title: "Paper broker", rawJson: broker ?? {} })}
        >
          {!broker ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                {
                  k: "policy",
                  v: <StatusBadge raw={asString(broker.policy_status) ?? "—"} />,
                },
              ]}
            />
          )}
        </Pane>

        <Pane
          title="Compute / GPU (advisory)"
          dense
          onInspect={() => openInspector({ title: "Compute", rawJson: compute ?? {} })}
        >
          {!compute ? (
            <p className="muted">—</p>
          ) : (
            <TermKV
              rows={[
                { k: "readiness", v: asString(compute.research_compute_readiness) ?? "—" },
                {
                  k: "gpu",
                  v: String((compute.gpu_probe as { gpu_available?: boolean } | undefined)?.gpu_available ?? "—"),
                },
              ]}
            />
          )}
        </Pane>

        <Pane title="Legacy demo manifest" dense onInspect={() => openInspector({ title: "Demo manifest", rawJson: demo ?? {} })}>
          {!demo || demo.status === "NOT_PRESENT" ? (
            <p className="muted">Optional: scripts/run_research_os_demo.py (older layout).</p>
          ) : (
            <TermKV
              rows={[
                { k: "status", v: asString(demo.status) ?? "—" },
                { k: "run_id", v: asString(demo.run_id) ?? "—" },
                { k: "path", v: asString(demo.artifact_path) ?? "—" },
              ]}
            />
          )}
        </Pane>

        {root && <JsonDetails summary="Full /ui/research-os/status" data={root} />}
      </div>
    </main>
  );
}
