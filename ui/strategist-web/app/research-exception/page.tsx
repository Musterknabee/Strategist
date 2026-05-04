"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsExceptionLatest } from "@/hooks/useUiResearchOsException";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchExceptionPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsExceptionLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.residual_warnings) : [];
  const blockers = latest ? asStringArray(latest.residual_blockers) : [];
  const constraints = latest ? asStringArray(latest.constraints) : [];
  const followups = latest ? asStringArray(latest.recommended_followups) : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-exception",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `EXCEPTION ${asString(latest.status) ?? "UNKNOWN"} · ${asString(latest.decision) ?? "UNKNOWN"}`
          : "NO_RESEARCH_OS_EXCEPTION_RECORD",
      },
    ],
    [blockers.length, degraded.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Exceptions</h1>
          <p className="muted">Time-bounded governed exceptions · no bypass of BLOCK evidence · no live trading</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Exceptions are annotations, not authority</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          ACTIVE means a WARN-level policy gate was acknowledged with constraints. BLOCK/EMPTY gates are not overridden by this page.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest exception" dense onInspect={() => openInspector({ title: "Research exception", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/exceptions/latest</p>}
          {!latest ? (
            <p className="muted">No exception record — run <code className="json-preview">strategy-validator-research-os-exception request --rationale "..." --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "exception_id", v: asString(latest.exception_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "decision", v: <StatusBadge raw={asString(latest.decision) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "operator_id", v: asString(latest.operator_id) ?? "—" },
                { k: "expires_at_utc", v: asString(latest.expires_at_utc) ?? "—" },
                { k: "source_gate", v: asString(latest.source_policy_gate_id) ?? "—" },
                { k: "gate_decision", v: <StatusBadge raw={asString(latest.source_policy_gate_decision) ?? "—"} /> },
                { k: "exception_spine", v: (asString(latest.exception_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-exception request --rationale "Paper-only restricted evidence acknowledged" --ttl-hours 24 --overwrite --json
          </pre>
        </Pane>

        <Pane title="Rationale" dense>
          <p className="muted">{asString(latest?.rationale) ?? "No rationale indexed."}</p>
        </Pane>

        <Pane title="Constraints" dense>
          {constraints.length ? <JsonDetails summary="constraints" data={constraints} /> : <p className="muted">No constraints indexed.</p>}
        </Pane>

        <Pane title="Covered / residual evidence" dense>
          <JsonDetails summary="covered_warnings" data={latest?.covered_warnings ?? []} />
          {warnings.length ? <JsonDetails summary="residual_warnings" data={warnings} /> : <p className="muted">No residual warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="residual_blockers" data={blockers} /> : <p className="muted">No residual blockers indexed.</p>}
        </Pane>

        <Pane title="Followups" dense>
          {followups.length ? <JsonDetails summary="recommended_followups" data={followups} /> : <p className="muted">No followups indexed.</p>}
        </Pane>
      </div>
    </main>
  );
}
