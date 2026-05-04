"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchOsPolicyGateLatest } from "@/hooks/useUiResearchOsPolicyGate";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type InputRow = Record<string, unknown> & { __id: string };
type RuleRow = Record<string, unknown> & { __id: string };

export default function ResearchPolicyGatePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiResearchOsPolicyGateLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const warnings = latest ? asStringArray(latest.warnings) : [];
  const blockers = latest ? asStringArray(latest.blockers) : [];
  const actions = latest ? asStringArray(latest.recommended_operator_actions) : [];

  const inputs: InputRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.inputs) ? latest.inputs : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.input_id) ?? "input"}-${i}` };
      })
      .filter((x): x is InputRow => x !== null);
  }, [latest]);

  const rules: RuleRow[] = useMemo(() => {
    const raw = Array.isArray(latest?.rules) ? latest.rules : [];
    return raw
      .map((item, i) => {
        const r = asRecord(item);
        if (!r) return null;
        return { ...r, __id: `${asString(r.rule_id) ?? "rule"}-${i}` };
      })
      .filter((x): x is RuleRow => x !== null);
  }, [latest]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "research-policy-gate",
        ts: asString(root?.generated_at_utc),
        severity: blockers.length ? "bad" : degraded.length || warnings.length ? "warn" : "ok",
        text: latest
          ? `POLICY_GATE ${asString(latest.decision) ?? "UNKNOWN"} · blockers=${latest.blocker_count ?? 0} warnings=${latest.warning_count ?? 0}`
          : "NO_RESEARCH_OS_POLICY_GATE_REPORT",
      },
    ],
    [blockers.length, degraded.length, latest, root, warnings.length],
  );
  useTerminalPageBind(tape, []);

  const inputCols: DenseColumn<InputRow>[] = [
    { key: "input", header: "Input", cell: (r) => asString(r.input_id) ?? "—" },
    { key: "category", header: "Category", cell: (r) => <StatusBadge raw={asString(r.category) ?? "—"} /> },
    { key: "exists", header: "Exists", cell: (r) => String(Boolean(r.exists)) },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status_hint) ?? asString(r.decision_hint) ?? asString(r.verification_status_hint) ?? "—"} /> },
    { key: "trust", header: "Trust", cell: (r) => <StatusBadge raw={asString(r.trust_banner_hint) ?? "—"} /> },
    { key: "sha", header: "SHA", cell: (r) => (asString(r.file_sha256) ?? "—").slice(0, 12) },
    { key: "warn", header: "Warn", cell: (r) => String(r.warnings_count ?? 0) },
    { key: "block", header: "Block", cell: (r) => String(r.blockers_count ?? 0) },
  ];

  const ruleCols: DenseColumn<RuleRow>[] = [
    { key: "rule", header: "Rule", cell: (r) => asString(r.rule_id) ?? "—" },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status) ?? "—"} /> },
    { key: "severity", header: "Severity", cell: (r) => <StatusBadge raw={asString(r.severity) ?? "—"} /> },
    { key: "message", header: "Message", cell: (r) => asString(r.message) ?? "—" },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Research Policy Gate</h1>
          <p className="muted">PASS/WARN/BLOCK operator posture · evidence-only · no live trading · no deployment approval</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>Policy gate is advisory governance evidence</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          PASS means the current evidence spine is internally consistent for paper-only operator review. It does not approve deployment, broker orders, or profitability claims.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Gate summary" dense onInspect={() => openInspector({ title: "Research policy gate", rawJson: q.data ?? {} })}>
          {q.isError && <p className="term-page__banner">Could not load /ui/research-os/policy-gate/latest</p>}
          {!latest ? (
            <p className="muted">No policy gate report — run <code className="json-preview">strategy-validator-research-os-policy-gate build --overwrite --json</code>.</p>
          ) : (
            <TermKV
              rows={[
                { k: "gate_id", v: asString(latest.gate_id) ?? "—" },
                { k: "decision", v: <StatusBadge raw={asString(latest.decision) ?? "—"} /> },
                { k: "trust_banner", v: <StatusBadge raw={asString(latest.trust_banner) ?? "—"} /> },
                { k: "required_inputs", v: `${latest.present_input_count ?? 0}/${latest.required_input_count ?? 0}` },
                { k: "warnings", v: String(latest.warning_count ?? 0) },
                { k: "blockers", v: String(latest.blocker_count ?? 0) },
                { k: "gate_spine", v: (asString(latest.gate_spine_sha256) ?? "—").slice(0, 24) },
                { k: "manifest", v: (asString(latest.manifest_sha256) ?? "—").slice(0, 24) },
              ]}
            />
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-research-os-policy-gate build --overwrite --json
          </pre>
        </Pane>

        <Pane title="Recommended operator actions" dense>
          {actions.length ? <JsonDetails summary="actions" data={actions} /> : <p className="muted">No action items indexed.</p>}
        </Pane>

        <Pane title="Warnings / blockers" dense>
          {warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No policy warnings indexed.</p>}
          {blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No policy blockers indexed.</p>}
        </Pane>

        <Pane title="Rules" dense>
          <DenseTable columns={ruleCols} rows={rules} rowKey={(r) => r.__id} onRowClick={(r) => openInspector({ title: `Policy rule · ${asString(r.rule_id) ?? "rule"}`, rawJson: r })} />
        </Pane>

        <Pane title="Evidence inputs" dense>
          <DenseTable columns={inputCols} rows={inputs} rowKey={(r) => r.__id} onRowClick={(r) => openInspector({ title: `Policy input · ${asString(r.input_id) ?? "input"}`, rawJson: r })} />
        </Pane>
      </div>
    </main>
  );
}
