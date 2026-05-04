"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsHandoffLatest } from "@/hooks/useUiResearchOsHandoff";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchHandoffPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsHandoffLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const checklist = Array.isArray(latest?.checklist) ? latest.checklist.map((x) => asRecord(x)) : [];
  const refs = Array.isArray(latest?.source_refs) ? latest.source_refs.map((x) => asRecord(x)) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const constraints = latest ? asStringArray(latest.handoff_constraints) : [];
  const followups = latest ? asStringArray(latest.remaining_followups) : [];
  const commands = latest ? asStringArray(latest.required_operator_commands) : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-handoff",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : warnings.length ? "warn" : "ok",
        text: latest
          ? `HANDOFF ${asString(latest.status) ?? "UNKNOWN"} · decision=${asString(latest.decision) ?? "UNKNOWN"}`
          : "NO_RESEARCH_OS_HANDOFF_PACK",
      },
    ],
    [blockers.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Handoff</h1>
          <p className="muted">Single-tenant operator handoff pack · not deployment approval · no trading authority</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Handoff evidence is not DEPLOYMENT_APPROVED</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page summarizes the evidence pack for release review. It does not approve deployment, enable live trading, or authorize broker orders.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest handoff pack" dense onInspect={() => openInspector({ title: "Research handoff", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/handoff/latest</p>}
          {!latest ? (
            <p className="muted">No handoff pack — run <code className="json-preview">strategy-validator-research-os-handoff build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "handoff_id", v: asString(latest.handoff_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "decision", v: <StatusBadge raw={asString(latest.decision) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "handoff_ready", v: String(Boolean(latest.handoff_ready)) },
                { k: "restricted_handoff", v: String(Boolean(latest.restricted_handoff)) },
                { k: "deployment_approved", v: String(Boolean(latest.deployment_approved)) },
                { k: "release_decision", v: <StatusBadge raw={asString(latest.source_release_readiness_decision) ?? "—"} /> },
                { k: "policy_gate", v: <StatusBadge raw={asString(latest.source_policy_gate_decision) ?? "—"} /> },
                { k: "exception_status", v: <StatusBadge raw={asString(latest.source_exception_status) ?? "—"} /> },
                { k: "checklist", v: `${checklist.length} items` },
                { k: "handoff_spine", v: (asString(latest.handoff_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-handoff build --artifact-root artifacts --overwrite --json
          </pre>
        </Pane>

        <Pane title="Checklist" dense>
          {checklist.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead><tr><th>status</th><th>item</th><th>source</th><th>warnings</th><th>blockers</th></tr></thead>
                <tbody>
                  {checklist.map((item) => (
                    <tr key={asString(item.item_id) ?? JSON.stringify(item)}>
                      <td><StatusBadge raw={asString(item.status) ?? "—"} /></td>
                      <td>{asString(item.title) ?? "—"}</td>
                      <td>{asString(item.source) ?? "—"}</td>
                      <td>{asStringArray(item.warnings).length}</td>
                      <td>{asStringArray(item.blockers).length}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">No checklist items.</p>}
        </Pane>

        <Pane title="Source refs" dense>
          {refs.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead><tr><th>label</th><th>present</th><th>status</th><th>decision</th><th>digest</th></tr></thead>
                <tbody>
                  {refs.map((ref) => (
                    <tr key={asString(ref.label) ?? JSON.stringify(ref)}>
                      <td>{asString(ref.label) ?? "—"}</td>
                      <td>{String(Boolean(ref.present))}</td>
                      <td><StatusBadge raw={asString(ref.status_hint) ?? "—"} /></td>
                      <td><StatusBadge raw={asString(ref.decision_hint) ?? "—"} /></td>
                      <td>{(asString(ref.manifest_sha256) ?? "—").slice(0, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">No source refs.</p>}
        </Pane>

        <Pane title="Constraints / followups / commands" dense>
          <JsonDetails title="Constraints" value={constraints} />
          <JsonDetails title="Remaining followups" value={followups} />
          <JsonDetails title="Required operator commands" value={commands} />
          <JsonDetails title="Warnings" value={warnings} />
          <JsonDetails title="Blockers" value={blockers} />
        </Pane>
      </div>
    </main>
  );
}
