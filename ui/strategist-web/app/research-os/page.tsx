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

  const gauntlet = root?.gauntlet_latest != null ? asRecord(root.gauntlet_latest as object) : null;
  const paper = root?.paper_tracking_latest != null ? asRecord(root.paper_tracking_latest as object) : null;
  const promo = root?.promotion_packet_latest != null ? asRecord(root.promotion_packet_latest as object) : null;
  const broker = root?.paper_broker_status != null ? asRecord(root.paper_broker_status as object) : null;
  const compute = root?.compute_status != null ? asRecord(root.compute_status as object) : null;
  const demo = root?.demo_manifest != null ? asRecord(root.demo_manifest as object) : null;
  const provider = root?.provider_ingestion_latest != null ? asRecord(root.provider_ingestion_latest as object) : null;
  const daily = root?.daily_tracking_latest != null ? asRecord(root.daily_tracking_latest as object) : null;
  const cpcv = root?.cpcv_latest != null ? asRecord(root.cpcv_latest as object) : null;
  const portfolio = root?.portfolio_allocation_latest != null ? asRecord(root.portfolio_allocation_latest as object) : null;

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research OS</h1>
          <p className="muted">
            Consolidated read-plane status · evidence only · no live trading · no broker orders from browser
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
                { k: "summary_path", v: asString(gauntlet.summary_path) ?? "—" },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.5rem", fontSize: "10px" }}>
            python scripts/run_research_os_demo.py --output-root artifacts/research_os_demo --run-id my-demo --overwrite
            --skip-benchmark --json
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
                {
                  k: "lifecycle",
                  v: asString((paper.latest as { lifecycle_state?: string }).lifecycle_state) ?? "—",
                },
                {
                  k: "promotion_review_ready",
                  v: String((paper.latest as { promotion_review_ready?: boolean }).promotion_review_ready ?? false),
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
              ]}
            />
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

        <Pane title="Demo manifest" dense onInspect={() => openInspector({ title: "Demo manifest", rawJson: demo ?? {} })}>
          {!demo || demo.status === "NOT_PRESENT" ? (
            <p className="muted">No demo_manifest.json — run scripts/run_research_os_demo.py first.</p>
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
