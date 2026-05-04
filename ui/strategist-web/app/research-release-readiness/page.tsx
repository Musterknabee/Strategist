"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsReleaseReadinessLatest } from "@/hooks/useUiResearchOsReleaseReadiness";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchReleaseReadinessPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsReleaseReadinessLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const criteria = Array.isArray(latest?.criteria)
    ? latest.criteria.map((x) => asRecord(x)).filter((r): r is Record<string, unknown> => r !== null)
    : [];
  const degraded = root ? asStringArray(root.degraded) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const followups = latest ? asStringArray(latest.required_followups) : [];
  const commands = latest ? asStringArray(latest.recommended_review_commands) : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-release-readiness",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `RELEASE_READINESS ${asString(latest.status) ?? "UNKNOWN"} · decision=${asString(latest.decision) ?? "UNKNOWN"}`
          : "NO_RESEARCH_OS_RELEASE_READINESS_REPORT",
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
          <h1>Research Release Readiness</h1>
          <p className="muted">Single-tenant release-review posture · not deployment approval · no trading authority</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Review readiness is not DEPLOYMENT_APPROVED</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page classifies whether the latest Research OS evidence can enter a release review. It does not approve deployment or enable live trading.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest release-readiness report" dense onInspect={() => openInspector({ title: "Research release readiness", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/release-readiness/latest</p>}
          {!latest ? (
            <p className="muted">No release-readiness report — run <code className="json-preview">strategy-validator-research-os-release-readiness build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "report_id", v: asString(latest.report_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "decision", v: <StatusBadge raw={asString(latest.decision) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "release_review_ready", v: String(Boolean(latest.release_review_ready)) },
                { k: "deployment_approved", v: String(Boolean(latest.deployment_approved)) },
                { k: "gate_decision", v: <StatusBadge raw={asString(latest.source_policy_gate_decision) ?? "—"} /> },
                { k: "exception_status", v: <StatusBadge raw={asString(latest.source_exception_status) ?? "—"} /> },
                { k: "P0/P1 open", v: `${String(latest.p0_open_count ?? 0)} / ${String(latest.p1_open_count ?? 0)}` },
                { k: "open remediation", v: String(latest.open_remediation_count ?? "—") },
                { k: "readiness_spine", v: (asString(latest.release_readiness_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-release-readiness build --artifact-root artifacts --overwrite --json
          </pre>
        </Pane>

        <Pane title="Criteria" dense>
          {criteria.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead>
                  <tr><th>status</th><th>criterion</th><th>source</th><th>warnings</th><th>blockers</th></tr>
                </thead>
                <tbody>
                  {criteria.map((c) => (
                    <tr key={asString(c.criterion_id) ?? JSON.stringify(c)}>
                      <td><StatusBadge raw={asString(c.status) ?? "—"} /></td>
                      <td>{asString(c.title) ?? "—"}</td>
                      <td>{asString(c.source) ?? "—"}</td>
                      <td>{asStringArray(c.warnings).length}</td>
                      <td>{asStringArray(c.blockers).length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">No criteria indexed.</p>}
        </Pane>

        <Pane title="Followups / commands" dense>
          {followups.length ? <JsonDetails summary="required_followups" data={followups} /> : <p className="muted">No required followups.</p>}
          {commands.length ? <JsonDetails summary="review_commands" data={commands} /> : <p className="muted">No commands indexed.</p>}
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No report warnings.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No report blockers.</p>}
        </Pane>
      </div>
    </main>
  );
}
