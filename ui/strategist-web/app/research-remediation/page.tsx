"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsRemediationLatest } from "@/hooks/useUiResearchOsRemediation";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function ResearchRemediationPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsRemediationLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const items = Array.isArray(latest?.items) ? latest.items.map((x) => asRecord(x)) : [];
  const degraded = root ? asStringArray(root.degraded) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const actions = latest ? asStringArray(latest.recommended_next_actions) : [];

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-remediation",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `REMEDIATION ${asString(latest.status) ?? "UNKNOWN"} · items=${String(latest.item_count ?? 0)}`
          : "NO_RESEARCH_OS_REMEDIATION_PLAN",
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
          <h1>Research Remediation</h1>
          <p className="muted">Read-plane action queue · evidence remediation only · no live trading authority</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Remediation is guidance, not approval</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          This page converts policy gate, exception, catalog, and drift signals into an operator action queue. It does not bypass blockers.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Latest remediation plan" dense onInspect={() => openInspector({ title: "Research remediation", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/remediation/latest</p>}
          {!latest ? (
            <p className="muted">No remediation plan — run <code className="json-preview">strategy-validator-research-os-remediation build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "plan_id", v: asString(latest.plan_id) ?? "—" },
                { k: "status", v: <StatusBadge raw={asString(latest.status) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "source_gate", v: asString(latest.source_policy_gate_id) ?? "—" },
                { k: "gate_decision", v: <StatusBadge raw={asString(latest.source_policy_gate_decision) ?? "—"} /> },
                { k: "items", v: String(latest.item_count ?? "—") },
                { k: "open", v: String(latest.open_count ?? "—") },
                { k: "blocked", v: String(latest.blocked_count ?? "—") },
                { k: "waived", v: String(latest.waived_count ?? "—") },
                { k: "remediation_spine", v: (asString(latest.remediation_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-remediation build --artifact-root artifacts --overwrite --json
          </pre>
        </Pane>

        <Pane title="Priority / category counts" dense>
          <JsonDetails summary="priority_counts" data={latest?.priority_counts ?? {}} />
          <JsonDetails summary="category_counts" data={latest?.category_counts ?? {}} />
        </Pane>

        <Pane title="Recommended next actions" dense>
          {actions.length ? <JsonDetails summary="commands" data={actions} /> : <p className="muted">No remediation actions indexed.</p>}
        </Pane>

        <Pane title="Action queue" dense>
          {items.length ? (
            <div className="terminal-table-wrap">
              <table className="terminal-table">
                <thead>
                  <tr><th>priority</th><th>status</th><th>category</th><th>title</th><th>source</th></tr>
                </thead>
                <tbody>
                  {items.slice(0, 80).map((item) => (
                    <tr key={asString(item.item_id) ?? JSON.stringify(item)}>
                      <td><StatusBadge raw={asString(item.priority) ?? "—"} /></td>
                      <td><StatusBadge raw={asString(item.status) ?? "—"} /></td>
                      <td>{asString(item.category) ?? "—"}</td>
                      <td>{asString(item.title) ?? "—"}</td>
                      <td>{asString(item.source) ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="muted">No remediation items indexed.</p>
          )}
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No plan warnings.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No plan blockers.</p>}
        </Pane>
      </div>
    </main>
  );
}
