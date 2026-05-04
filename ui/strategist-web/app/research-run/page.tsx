"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsRunLatest } from "@/hooks/useUiResearchOsRun";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type StepRow = Record<string, unknown> & { __id: string };

export default function ResearchRunPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsRunLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];

  const steps: StepRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.steps) ? latest.steps : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.step_id) ?? "step"}-${i}` };
      })
      .filter((x): x is StepRow => x !== null);
  }, [latest]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-run",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `RUN ${asString(latest.status) ?? "UNKNOWN"} · steps=${steps.length}`
          : "NO_RESEARCH_OS_OPERATOR_RUN",
      },
    ],
    [blockers.length, degraded.length, latest, root, steps.length, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<StepRow>[] = [
    { key: "step_id", header: "Step", cell: (r) => <code>{asString(r.step_id) ?? "—"}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status) ?? "—"} /> },
    { key: "artifact", header: "Artifact", cell: (r) => (asString(r.artifact_path) ?? "—").split("/").slice(-2).join("/") },
    { key: "warnings", header: "Warn", cell: (r) => String(asStringArray(r.warnings).length) },
    { key: "blockers", header: "Block", cell: (r) => String(asStringArray(r.blockers).length) },
    { key: "sha", header: "SHA", cell: (r) => (asString(r.artifact_sha256) ?? "—").slice(0, 16) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Run</h1>
          <p className="muted">Operator sequence · closure → attestation → briefing → export · read-plane only</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Operator run is evidence orchestration, not execution approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          The run manifest records the paper-only evidence sequence and digest links. It does not authorize live trading, broker orders, or deployment approval.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Run summary" dense onInspect={() => openInspector({ title: "Research operator run", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/run/latest</p>}
          {!latest ? (
            <p className="muted">No operator run — run <code className="json-preview">strategy-validator-research-os-run run --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "run_id", v: asString(latest.run_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "steps", v: String(steps.length) },
                { k: "operator_run_spine", v: (asString(asRecord(latest.digests)?.operator_run_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest_sha256", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-run run --overwrite --json
          </pre>
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No operator-run warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No operator-run blockers indexed.</p>}
        </Pane>

        <Pane title="Run steps" dense>
          <DenseTable
            columns={cols}
            rows={steps}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Run step · ${asString(r.step_id) ?? "step"}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
